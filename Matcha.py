import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.metrics.pairwise import cosine_similarity
pd.options.mode.chained_assignment = None


client_id = 'ca8668888ab6408b8da70b6385815a3e'; # Your client id
client_secret = 'bfd03aef2fc9405b89e002888d921d84'; # Your secret

#importing dataframe
df = pd.read_pickle('feature_set.pkl')

#Spotify Authentication to get client credentials
def Spotifyauth():
    scope='user-library-read user-playlist-modify-public'
    auth_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    token=spotipy.util.prompt_for_user_token(scope,client_id=client_id,client_secret=client_secret,redirect_uri='http://192.168.1.7:8501/')
    sp=spotipy.Spotify(auth=token)
    sp.__init__(auth=token,auth_manager=auth_manager)
    return sp
 

#To access spotify database without user authorization
def NoSpotifyauth():
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


#To get all the songs from user playlist that are available in our dataset
def user_create_necessary_outputs(playlist_name,id_dic,df,sp):
    playlist=pd.DataFrame()
    playlist_name=playlist_name
    for ix,i in enumerate(sp.playlist(id_dic[playlist_name])['tracks']['items']):
        playlist.loc[ix,'artist']=i['track']['artists'][0]['name']
        playlist.loc[ix,'name']=i['track']['name']
        playlist.loc[ix,'id']=i['track']['id']#['uri'].split(':')[2]
        playlist.loc[ix,'url']=i['track']['album']['images'][1]['url']
        playlist.loc[ix,'date_added']=i['added_at']
    playlist['date_added']=pd.to_datetime(playlist['date_added'])
    playlist=playlist[playlist['id'].isin(df['id'].values)].sort_values('date_added',ascending=False)
    return playlist


#To get all songs from non user playlist that are available in our dataset
def nonuser_create_necessary_outputs(link,df,sp):
    playlist=pd.DataFrame()
    id=link[34:]
    
    for ix,i in enumerate(sp.playlist(id)['tracks']['items']):
        playlist.loc[ix,'artist']=i['track']['artists'][0]['name']
        playlist.loc[ix,'name']=i['track']['name']
        playlist.loc[ix,'id']=i['track']['id']#['uri'].split(':')[2]
        playlist.loc[ix,'url']=i['track']['album']['images'][0]['url']
        playlist.loc[ix,'date_added']=i['added_at']
    playlist['date_added']=pd.to_datetime(playlist['date_added'])
    playlist=playlist[playlist['id'].isin(df['id'].values)].sort_values('date_added',ascending=False)

    return playlist


#To generate playlist vector
def generate_playlist_vector(complete_feature_set,playlist_df,weight_factor):
    complete_feature_set_playlist=complete_feature_set[complete_feature_set['id'].isin(playlist_df['id'].values)]
    complete_feature_set_playlist=complete_feature_set_playlist.merge(playlist_df[['id','date_added']], on='id',how='inner')
    complete_feature_set_nonplaylist=complete_feature_set[~complete_feature_set['id'].isin(playlist_df['id'].values)]
    
    playlist_feature_set=complete_feature_set_playlist.sort_values('date_added',ascending=False)
    
    most_recent_date=playlist_feature_set.iloc[0,-1]
    
    for ix,row in playlist_feature_set.iterrows():
        playlist_feature_set.loc[ix,'months_from_recent']=int((most_recent_date.to_pydatetime()-row.iloc[-1].to_pydatetime()).days/30)
        
    playlist_feature_set['weight']=playlist_feature_set['months_from_recent'].apply(lambda x: weight_factor ** (-x))
    
    playlist_feature_set_weighted=playlist_feature_set.copy()
    
    playlist_feature_set_weighted.update(playlist_feature_set_weighted.iloc[:,:-7].mul(playlist_feature_set_weighted.weight,0))
    playlist_feature_set_weighted_final=playlist_feature_set_weighted.iloc[:,:-7]

    return playlist_feature_set_weighted_final.sum(axis=0),complete_feature_set_nonplaylist


#To generate recommendations
def generate_recs(features,nonplaylist_features,sp):
    a=nonplaylist_features.drop(columns=['id','name','artists','id_artists'])
    b=features.values.reshape(1,-1)
    temp=pd.DataFrame()
    temp['id']=nonplaylist_features['id']
    temp['name']=nonplaylist_features['name']
    temp['artists']=nonplaylist_features['artists']
    temp['id_artists']=nonplaylist_features['id_artists']
    temp['sim']=cosine_similarity(a.values,b)[:,0]
    recommend=(temp.sort_values('sim',ascending=False)).head(15)
    recommend['url']=recommend['id'].apply(lambda x: sp.track(x)['album']['images'][1]['url'])
    recommend['preview_url']=recommend['id'].apply(lambda x:sp.track(x)['preview_url'])
    recommend.reset_index(drop=0,inplace=True)
    return recommend

#To get all playlists available in user's library
def GetUserPlaylistName(sp):
    id_name={}
    list_photo={}
    user_playlist=sp.current_user_playlists(50,0)
    playlists=pd.DataFrame(user_playlist)
    play=pd.Series(playlists['items'])
    for i in range(len(play)):
        id_name[play[i]['name']]=play[i]['uri'].split(':')[2]
        img=pd.DataFrame(play[i]['images'])
        list_photo[play[i]['uri'].split(':')[2]]=img['url'][0]
    return id_name,list_photo


#display songs with their cover art,links and playback
def ShowRecommend(rec_playlist):
    for i in range(len(rec_playlist)):
         with st.container():
            col1, col2 ,col3 = st.columns([5,20,10])
            col1.image(rec_playlist['url'][i], width=None)
            with col2:
                st.subheader(rec_playlist['name'][i]+" by " +rec_playlist['artists'][i])
                Song='[Song link]({link})'.format(link='https://open.spotify.com/track/'+rec_playlist['id'][i])
                st.write(Song)
                artist='[Artist link]({link})'.format(link='https://open.spotify.com/artist/'+rec_playlist['id_artists'][i])
                st.write(artist)
            with col3:
                if rec_playlist['preview_url'][i] is not None:
                    st.audio(rec_playlist['preview_url'][i],format='audio/mp3')
                else:
                    st.write('Track preview is not available :(')



#This page will be displayed if the user decides to login
def MainAfterLogin():
        sp=Spotifyauth()
        me=sp.me()
        st.header("Welcome "+me['display_name']+"!")
        st.subheader("Here are the playlists present on your profile:")
        name,photo=GetUserPlaylistName(sp)
        name['Select Your option']='Invalid'
        selection=st.selectbox(label="Select One of your Pre-Existing Playlists",options=name.keys(),index=(len(name)-1))
        if selection=='Select Your option':
            st.write('WARNING: Please select a valid option')
        else:
            st.write("Your selected playlist is : '" + selection+"'")
            
            #Generating a dataframe of songs in the intersection of selected playlist and our dataset
            playlist=user_create_necessary_outputs(selection,name,df,sp)
            if playlist.empty:
                st.write("Sorry, there are no songs that intersect your provided playlist and out dataset")
                st.wrtie("Please try again with another playlist")
            else:
                st.write("Following songs present in your playlist will be used to generate recommendations")
                st.write(pd.DataFrame({"Songs by Artists" : playlist['name']+" by "+playlist['artist']}))
                #creating a playlist vector for cosine similarity
                playlist_vector,nondf=generate_playlist_vector(df,playlist,1.09)
                if st.button("Generate Recommendations"):
                    #generating recommendations
                    st.subheader("Following are the recommended songs:")
                    recommend=generate_recs(playlist_vector,nondf,sp)
                    ShowRecommend(recommend)

    
                  
                    


#This page will be displayed if user decides to be anonymous
def MainAfterNoLogin():
        sp=NoSpotifyauth()   
        st.header("Welcome Human !")

        #recommendations by playlist useing my dataset
        link=st.text_input("Enter playlist link")
        if len(link)==0:
            st.write("Please enter a link before proceeding")
        else:
            playlist=nonuser_create_necessary_outputs(link,df,sp)
            if playlist.empty:
                st.write("Sorry, there are no songs that intersect your provided playlist and out dataset")
                st.write("Please try again with another playlist")
            else:
                st.write("Following songs present in your provided playlist will be used to generate recommendations")
                st.write(pd.DataFrame({"Songs by Artists" : playlist['name']+" by "+playlist['artist']}))
                #creating a playlist vector for cosine similarity
                playlist_vector,nondf=generate_playlist_vector(df,playlist,1.09)
                if st.button("Generate Recommendations"):
                        #generating recommendations
                        st.subheader("Following are the recommended songs:")
                        recommend=generate_recs(playlist_vector,nondf,sp)
                        ShowRecommend(recommend)


        #recommendations from genres
        genres=sp.recommendation_genre_seeds()['genres']
        txt = st.multiselect(label='Select Genres to generate recommendations',options=genres)
        if len(txt)==0:
            st.write("Please select atleast one genre.")
            return
        else:
            st.write('You have selected the following genres:')
            for i in range(len(txt)):
                st.write("👉 " + txt[i])
            if st.button("Generate recommendation"):
                st.subheader("Following recommendations are generated: ")
                recommend=sp.recommendations(seed_genres=txt,limit=15)['tracks']
                for i in range(len(recommend)):
                    container = st.container()
                    col1, col2 ,col3= st.columns([5, 20,10])
                    with container:
                        with col1:
                            #showing all song cover art
                            st.image(recommend[i]['album']['images'][0]['url'], width=None)
                        with col2:
                            artist=recommend[i]['album']['artists'][0]
                            st.subheader(recommend[i]['name']+" by " + artist['name'])
                            Song='[Song link]({link})'.format(link=recommend[i]['external_urls']['spotify'])
                            st.write(Song)
                            Artist='[Artist link]({link})'.format(link=recommend[i]['artists'][0]['external_urls']['spotify'])
                            st.write(Artist)
                        with col3:
                            if recommend[i]['preview_url'] is not None:
                                st.audio(recommend[i]['preview_url'],format='audio/mp3')
                            else:
                                st.write('Track preview is not available :(')

        
                            
 
                    
def LoadTitle():
    image = 'images/logo.png'
    st.image(image, width=50)
    st.markdown('<h1 style="color: #507250;">Matcha !</h1>',unsafe_allow_html=True)




#Page setup
st.set_page_config(
   page_title="Matcha",
   page_icon="images/favicon.ico",
   layout="wide",
   initial_sidebar_state="expanded",
)


hide_st_style = """
            <style>
            header {visibility: hidden;}
            footer {visibility: hidden;}
            MainMenu {visibility: hidden;}
            </style>
           """
st.markdown(hide_st_style, unsafe_allow_html=True)
     

if __name__=='__main__':
    LoadTitle()
    st.markdown("""---""")
    st.sidebar.header("Choose your login method")
    selection = st.sidebar.selectbox(
    "How would you like to continue?",
    ("Home","With Spotify", "As Anonymous"))
    if selection=="Home":
        st.subheader("Where we brew your recommendations 🍵")
        st.write("Made By Astha Barwal as a submission for Microsoft Engage'22")
        st.write("[Github Repo](https://github.com/asthabarwal/Matcha_Recomendation)")
    if selection=="With Spotify":
        MainAfterLogin()
    if selection=="As Anonymous":
        MainAfterNoLogin()
    

    
    