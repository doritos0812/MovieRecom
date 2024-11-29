# -*- coding: utf-8 -*-
"""movie_recommand.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/177d_dYnmGYQydjymCTpn1NhoQ7DxcmTf
"""

import random
import pandas as pd
import numpy as np
import os, sys
import re

from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

from google.colab import drive

# 구글 드라이브와 연결
drive.mount('/content/drive')

mount_directory = "drive/MyDrive"

# 데이터 크기 설정 ex)latest-small, 32m, ...
dataset_volume = "32m"

# CSV 데이터 로드
df_ratings = pd.read_csv(f"{mount_directory}/ml-{dataset_volume}/ratings.csv")
df_movies = pd.read_csv(f"{mount_directory}/movies_processed_data/movies_processed_32m.csv")
df_tags = pd.read_csv(f"{mount_directory}/ml-{dataset_volume}/tags.csv")

df_ratings.drop(['timestamp'], axis=1, inplace=True)

# NaN 값을 빈 문자열로 대체
df_movies['director'] = df_movies['director'].fillna('')
df_movies['actors'] = df_movies['actors'].fillna('')
df_movies['genres'] = df_movies['genres'].fillna('')

# Dataset의 User, Movie 수 확인
n_users = df_ratings.userId.unique().shape[0]
n_items = df_ratings.movieId.unique().shape[0]
print("num users: {}, num items:{}".format(n_users, n_items))

movie_rate = dict()

for row in df_ratings.itertuples(index = False):
  user_id, movie_id, rate = row
  if movie_id not in movie_rate:
    movie_rate[movie_id] = [0, 0]
  movie_rate[movie_id][0] += rate
  movie_rate[movie_id][1] += 1

for key, value in movie_rate.items():
  value1 = value[0] / value[1]
  movie_rate[key] = [round(value1, 3),value[1]]

rates = dict()
rates['movieId'] = []
rates['score'] = []
rates['count'] = []
for key, value in movie_rate.items():
  rates['movieId'].append(key)
  rates['score'].append(value[0])
  rates['count'].append(value[1])

scores = pd.DataFrame(rates)
scores

df_movies = pd.merge(df_movies, scores, on='movieId')

df_movies.head(4)

m = df_movies['count'].quantile(0.89)

m

C = df_movies['score'].mean()

print(C)
print(m)

def weighted_rating(x, m=m, C=C):
    v = x['count']
    R = x['score']

    return ( v / (v+m) * R ) + (m / (m + v) * C)

df_movies['weighted_score'] = df_movies.apply(weighted_rating, axis = 1)

processed_data = df_movies.loc[df_movies['count'] >= m]

# 기존 index를 무시하고 새로운 index 설정
processed_data = processed_data.reset_index(drop=True)

processed_data

count_vector_triple = CountVectorizer(ngram_range=(1, 3))
count_vector_once = CountVectorizer(ngram_range=(1, 1))

c_vector_genres = count_vector_triple.fit_transform(processed_data['genres'])
c_vector_genres

c_vector_director = count_vector_once.fit_transform(processed_data['director'])
c_vector_director

c_vector_actors = count_vector_triple.fit_transform(processed_data['actors'])
c_vector_actors

#코사인 유사도를 구한 벡터를 미리 저장
gerne_c_sim = cosine_similarity(c_vector_genres, c_vector_genres)

#코사인 유사도를 구한 벡터를 미리 저장
director_c_sim = cosine_similarity(c_vector_director, c_vector_director)

#코사인 유사도를 구한 벡터를 미리 저장
actors_c_sim = cosine_similarity(c_vector_actors, c_vector_actors)

# 가중치 설정
weights = [0.5, 0.1, 0.4]

# 가중치 합산
combined_similarity = (
    weights[0] * gerne_c_sim +
    weights[1] * director_c_sim +
    weights[2] * actors_c_sim
)

# 각 row에서 유사도를 정렬 (내림차순)
sorted_indices = combined_similarity.argsort()[:, ::-1]

# 결과 확인
print(sorted_indices)

def get_recommend_movie_list(df, movie_title, top=30):
    # 특정 영화와 비슷한 영화를 추천해야 하기 때문에 '특정 영화' 정보를 뽑아낸다.
    target_movie_index = df[df['title'] == movie_title].index.values

    #코사인 유사도 중 비슷한 코사인 유사도를 가진 정보를 뽑아낸다.
    sim_index = sorted_indices[target_movie_index, :top].reshape(-1)
    #본인을 제외
    sim_index = sim_index[sim_index != target_movie_index]

    #data frame으로 만들고 vote_count으로 정렬한 뒤 return
    result = df.iloc[sim_index].sort_values('weighted_score', ascending=False)[:20]
    return result

get_recommend_movie_list(processed_data, movie_title='Deadpool')

