"""
NLTK 자연어 처리 서비스 클래스
"""
import logging
from typing import List, Tuple, Dict, Optional, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.stem import PorterStemmer, LancasterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag, untag
from nltk import Text, FreqDist
from wordcloud import WordCloud
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def safe_execute(func, default=None, error_msg=""):
    """안전한 함수 실행 헬퍼"""
    try:
        return func()
    except Exception as e:
        logger.error(f"{error_msg}: {e}")
        return default if default is not None else ([] if isinstance(default, list) else "")


class NLPService:
    """NLTK 기반 자연어 처리 서비스"""
    
    def __init__(self):
        """초기화"""
        self._download_nltk_data()
        self.regex_tokenizer = RegexpTokenizer(r"[\w]+")
        self.porter_stemmer = PorterStemmer()
        self.lancaster_stemmer = LancasterStemmer()
        self.lemmatizer = WordNetLemmatizer()
    
    def _download_nltk_data(self):
        """NLTK 데이터 다운로드"""
        for data in ['book', 'punkt', 'wordnet', 'averaged_perceptron_tagger']:
            try:
                nltk.download(data, quiet=True)
            except:
                pass
    
    # ========== 말뭉치 관리 ==========
    def get_corpus_fileids(self, corpus_name: str = "gutenberg") -> List[str]:
        """말뭉치 파일 ID 목록 조회"""
        return safe_execute(
            lambda: getattr(nltk.corpus, corpus_name).fileids(),
            default=[],
            error_msg="말뭉치 파일 ID 조회"
        )
    
    def load_corpus_text(self, corpus_name: str, fileid: str) -> str:
        """말뭉치에서 텍스트 로드"""
        return safe_execute(
            lambda: getattr(nltk.corpus, corpus_name).raw(fileid),
            default="",
            error_msg="말뭉치 텍스트 로드"
        )
    
    # ========== 토큰 생성 ==========
    def tokenize_sentences(self, text: str) -> List[str]:
        """문장 단위 토큰 생성"""
        return safe_execute(lambda: sent_tokenize(text), default=[], error_msg="문장 토큰 생성")
    
    def tokenize_words(self, text: str) -> List[str]:
        """단어 단위 토큰 생성"""
        return safe_execute(lambda: word_tokenize(text), default=[], error_msg="단어 토큰 생성")
    
    def tokenize_regex(self, text: str, pattern: str = r"[\w]+") -> List[str]:
        """정규식 기반 토큰 생성"""
        return safe_execute(
            lambda: RegexpTokenizer(pattern).tokenize(text),
            default=[],
            error_msg="정규식 토큰 생성"
        )
    
    # ========== 형태소 분석 ==========
    def stem_porter(self, words: List[str]) -> List[str]:
        """Porter Stemmer 어간 추출"""
        return safe_execute(
            lambda: [self.porter_stemmer.stem(w) for w in words],
            default=[],
            error_msg="Porter Stemming"
        )
    
    def stem_lancaster(self, words: List[str]) -> List[str]:
        """Lancaster Stemmer 어간 추출"""
        return safe_execute(
            lambda: [self.lancaster_stemmer.stem(w) for w in words],
            default=[],
            error_msg="Lancaster Stemming"
        )
    
    def lemmatize(self, words: List[str], pos: Optional[str] = None) -> List[str]:
        """원형 복원"""
        return safe_execute(
            lambda: [self.lemmatizer.lemmatize(w, pos=pos) if pos else self.lemmatizer.lemmatize(w) for w in words],
            default=[],
            error_msg="Lemmatization"
        )
    
    # ========== 품사 태깅 ==========
    def pos_tag_text(self, text: str) -> List[Tuple[str, str]]:
        """텍스트 품사 태깅"""
        return safe_execute(
            lambda: pos_tag(word_tokenize(text)),
            default=[],
            error_msg="품사 태깅"
        )
    
    def pos_tag_tokens(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """토큰 리스트 품사 태깅"""
        return safe_execute(lambda: pos_tag(tokens), default=[], error_msg="품사 태깅")
    
    def filter_by_pos(self, tagged_list: List[Tuple[str, str]], pos: str) -> List[str]:
        """특정 품사만 필터링"""
        return [word for word, tag in tagged_list if tag == pos]
    
    def remove_tags(self, tagged_list: List[Tuple[str, str]]) -> List[str]:
        """품사 태그 제거"""
        return safe_execute(lambda: untag(tagged_list), default=[], error_msg="태그 제거")
    
    def create_pos_tokenizer(self, tagged_list: List[Tuple[str, str]]) -> List[str]:
        """품사 정보 포함 토크나이저 생성"""
        return ["/".join(pair) for pair in tagged_list]
    
    def get_pos_help(self, tag: str) -> str:
        """품사 태그 설명 조회"""
        try:
            nltk.help.upenn_tagset(tag)
            return f"품사 태그 '{tag}' 설명 출력"
        except:
            return ""
    
    # ========== Text 클래스 활용 ==========
    def create_text_object(self, tokens: List[str], name: str = "Text") -> Text:
        """NLTK Text 객체 생성"""
        return safe_execute(
            lambda: Text(tokens, name=name),
            default=Text([], name=name),
            error_msg="Text 객체 생성"
        )
    
    def plot_word_frequency(self, text: Text, num_words: int = 20):
        """단어 빈도 그래프"""
        safe_execute(lambda: text.plot(num_words) or plt.show(), error_msg="단어 빈도 그래프")
    
    def plot_dispersion(self, text: Text, words: List[str]):
        """단어 분산도 그래프"""
        safe_execute(lambda: text.dispersion_plot(words), error_msg="분산도 그래프")
    
    def find_concordance(self, text: Text, word: str, lines: int = 5):
        """단어 사용 위치 찾기"""
        safe_execute(lambda: text.concordance(word, lines=lines), error_msg="Concordance 검색")
    
    def find_similar_words(self, text: Text, word: str, num: int = 10):
        """유사 단어 찾기"""
        safe_execute(lambda: text.similar(word, num=num), error_msg="유사 단어 검색")
    
    def find_collocations(self, text: Text, num: int = 10):
        """연어 찾기"""
        safe_execute(lambda: text.collocations(num=num), error_msg="연어 검색")
    
    # ========== FreqDist 활용 ==========
    def create_freq_dist(self, tokens: List[str]) -> FreqDist:
        """빈도 분포 객체 생성"""
        return safe_execute(
            lambda: FreqDist(tokens),
            default=FreqDist([]),
            error_msg="FreqDist 생성"
        )
    
    def get_freq_stats(self, freq_dist: FreqDist, word: str) -> Dict[str, Any]:
        """단어 빈도 통계 조회"""
        return safe_execute(
            lambda: {
                "total_words": freq_dist.N(),
                "word_count": freq_dist[word],
                "word_frequency": freq_dist.freq(word)
            },
            default={"total_words": 0, "word_count": 0, "word_frequency": 0.0},
            error_msg="빈도 통계 조회"
        )
    
    def get_most_common(self, freq_dist: FreqDist, num: int = 10) -> List[Tuple[str, int]]:
        """가장 빈번한 단어 조회"""
        return safe_execute(
            lambda: freq_dist.most_common(num),
            default=[],
            error_msg="가장 빈번한 단어 조회"
        )
    
    def extract_names_from_text(self, text: str, stopwords: Optional[List[str]] = None) -> FreqDist:
        """텍스트에서 고유명사 추출 및 빈도 분석"""
        if stopwords is None:
            stopwords = ["Mr.", "Mrs.", "Miss", "Mr", "Mrs", "Dear"]
        return safe_execute(
            lambda: self.create_freq_dist([
                word for word, tag in self.pos_tag_tokens(self.regex_tokenizer.tokenize(text))
                if tag == "NNP" and word not in stopwords
            ]),
            default=FreqDist([]),
            error_msg="고유명사 추출"
        )
    
    # ========== 워드클라우드 ==========
    def generate_wordcloud(
        self, freq_dist: FreqDist, width: int = 1000, height: int = 600,
        background_color: str = "white", random_state: int = 0
    ) -> Optional[WordCloud]:
        """워드클라우드 생성"""
        return safe_execute(
            lambda: WordCloud(width=width, height=height, background_color=background_color, random_state=random_state)
            .generate_from_frequencies(freq_dist),
            default=None,
            error_msg="워드클라우드 생성"
        )
    
    def plot_wordcloud(self, wordcloud: WordCloud):
        """워드클라우드 시각화"""
        if wordcloud:
            safe_execute(
                lambda: plt.imshow(wordcloud) or plt.axis("off") or plt.show(),
                error_msg="워드클라우드 시각화"
            )
