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

class emotion_inference:
        
    def __init__(self):
        pass