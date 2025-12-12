import logging
import re
from typing import List, Tuple, Dict, Optional, Any
from pathlib import Path
import pandas as pd
import nltk  #보고서에 영어가 있을 수도 있을 수 있어서 남겨둠
from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.stem import PorterStemmer, LancasterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag, untag
from nltk import Text, FreqDist
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from konlpy.tag import Okt

logger = logging.getLogger(__name__)


class SamusungWordcloud:
        
    def __init__(self):
        self._download_nltk_data()
        self.okt = Okt()
    
    def _download_nltk_data(self):
        """NLTK 데이터 다운로드"""
        nltk_data_list = ['punkt_tab', 'punkt', 'wordnet', 'averaged_perceptron_tagger']
        for data in nltk_data_list:
            try:
                nltk.download(data, quiet=True)
            except Exception as e:
                logger.warning(f"NLTK 데이터 '{data}' 다운로드 중 경고: {e}")

    #자연어 처리리
    def text_process(self):
        freq_txt = self.find_freq()
        self.find_freq()    
        self.draw_wordcloud()    
        return {
            '전처리 결과 ' : '완료',
            'freq_txt' : freq_txt,
        }

    def read_file(self):
        #은,는,이,가가 등등 빼고 어간만 남김
        self.okt.pos("삼성전자 글로벌센터 전자사업부", stem=True)
        fname = Path(__file__).parent.parent / "data" / "kr-Report_2018.txt"
        with open(fname, 'r', encoding='utf-8') as f:
            text = f.read()
        return text
    
    def extract_nouns(self, text : str):
        temp = text.replace('\n', ' ') #줄바꿈 빼고
        tokenizer = re.compile(r'[^ ㄱ-ㅣ가-힣]+') #한글 외 모든 문자 제거 +한글자 이상.
        return tokenizer.sub('', temp)

    def change_token(self, texts):
        return word_tokenize(texts)

    def extract_noun(self):
        # 삼성전자의 스마트폰은 -> 삼성전자 스마트폰
        noun_tokens = []
        tokens = self.change_token(self.extract_nouns(self.read_file()))
        for i in tokens:
            pos = self.okt.pos(i)
            temp = [j[0] for j in pos if j[1] == 'Noun']
            #띄워쓰기 
            if len(''.join(temp)) > 1 :
                noun_tokens.append(''.join(temp))
        texts = ' '.join(noun_tokens)
        logger.info(texts[:100]) #콘솔에 100번째 단어까지 출력
        return texts

    def read_stopword(self):
        self.okt.pos("삼성전자 글로벌센터 전자사업부", stem=True)
        fname = Path(__file__).parent.parent / "data" / "stopwords.txt"
        with open(fname, 'r', encoding='utf-8') as f:
            stopwords = f.read()
        return stopwords

    def remove_stopword(self):
        texts = self.extract_noun()
        tokens = self.change_token(texts)
        # print('------- 1 명사 -------')
        # print(texts[:30])
        stopwords = self.read_stopword()
        # print('------- 2 스톱 -------')
        # print(stopwords[:30])
        # print('------- 3 필터 -------')
        texts = [text for text in tokens
                 if text not in stopwords]
        # print(texts[:30])
        return texts

    def find_freq(self):
        texts = self.remove_stopword()
        freqtxt = pd.Series(dict(FreqDist(texts))).sort_values(ascending=False)
        logger.info(freqtxt[:30])
        return freqtxt

    def draw_wordcloud(self):
        """워드클라우드 생성"""
        texts = self.remove_stopword()
        
        # save 폴더 경로 설정
        save_path = Path(__file__).parent.parent / "save"
        save_path.mkdir(parents=True, exist_ok=True)
        
        # 워드클라우드 생성
        font_path = Path(__file__).parent.parent / "data" / "D2Coding.ttf"
        wcloud = WordCloud(
            font_path=str(font_path),
            relative_scaling=0.2,
            background_color='white'
        ).generate(" ".join(texts))
        
        # 이미지 저장 (덮어쓰기 방식)
        filename = "samsung_wordcloud.png"
        file_path = save_path / filename
        
        # 기존 파일 확인 로그
        if file_path.exists():
            logger.info(f"기존 파일 발견. 덮어쓰기: {file_path}")
        else:
            logger.info(f"새 파일 생성: {file_path}")
        
        # 이미지 저장 (덮어쓰기)
        try:
            wcloud.to_file(str(file_path))
            logger.info(f"워드클라우드 저장 완료: {file_path}")
        except Exception as e:
            logger.error(f"워드클라우드 저장 중 오류: {e}")
            raise
        
        # 시각화 (선택사항)
        plt.figure(figsize=(12, 12))
        plt.imshow(wcloud, interpolation='bilinear')
        plt.axis('off')
        plt.close()  # plt.show() 대신 close()로 메모리 해제
        
        return str(file_path)