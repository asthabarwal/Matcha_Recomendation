# Matcha_Recomendation
Web application for recommending songs via content based filtering

Main App=> Matcha.py

Command to run app=> streamlit run Matcha.py

Dataset Available on => https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks

NOTE: Extract the pkl dataset from .rar file and download dataset from the above kaggle link before running any file



PS: i was not able to include raw dataset directly hence i have provided the link, it is still very much part of my project even though it is not included in files



Data_processing.ipnyb : processes the raw data available in the provided link and creates vector for each and every song based on genre,year,popularity and audio features(liveness,energy,tempo etc)

Recommendation.ipnyb : Fetches user's public playlists, generates a playlist vector based on the selected playlist and genertes recommendations from feature_set.pkl dataset


A little about the project:
- Song recommendation web app based of the principle of content 
- Using Tfidf Vectorizer and cosine similarity, vectors of each songs and similarity scores of each songs are created
- There is a login through spotify mode and an anonymous mode
