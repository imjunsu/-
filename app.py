import math
import re
import unicodedata
from io import StringIO

import numpy as np
import pandas as pd
import requests
import streamlit as st
import urllib3
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


st.set_page_config(
    page_title="축구 선수 시장가치 분석",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

FBREF_STANDARD_URL = "https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats"

BIG5_LEAGUES = {
    "eng Premier League": "프리미어리그",
    "es La Liga": "라리가",
    "it Serie A": "세리에 A",
    "de Bundesliga": "분데스리가",
    "fr Ligue 1": "리그 1",
    "Premier League": "프리미어리그",
    "La Liga": "라리가",
    "Serie A": "세리에 A",
    "Bundesliga": "분데스리가",
    "Ligue 1": "리그 1",
}

POSITION_KO = {
    "GK": "골키퍼",
    "DF": "수비수",
    "MF": "미드필더",
    "FW": "공격수",
    "FB": "풀백",
    "LB": "왼쪽 풀백",
    "RB": "오른쪽 풀백",
    "CB": "센터백",
    "DM": "수비형 미드필더",
    "CM": "중앙 미드필더",
    "AM": "공격형 미드필더",
    "LW": "왼쪽 윙어",
    "RW": "오른쪽 윙어",
}

NAME_KO = {
    "Son Heung-min": "손흥민",
    "Heung-min Son": "손흥민",
    "Kim Min-jae": "김민재",
    "Min-jae Kim": "김민재",
    "Lee Kang-in": "이강인",
    "Kang-in Lee": "이강인",
    "Hwang Hee-chan": "황희찬",
    "Hee-chan Hwang": "황희찬",
    "Kylian Mbappe": "킬리안 음바페",
    "Kylian Mbappé": "킬리안 음바페",
    "Erling Haaland": "엘링 홀란",
    "Harry Kane": "해리 케인",
    "Jude Bellingham": "주드 벨링엄",
    "Vinicius Junior": "비니시우스 주니오르",
    "Vinícius Júnior": "비니시우스 주니오르",
    "Lamine Yamal": "라민 야말",
    "Pedri": "페드리",
    "Gavi": "가비",
    "Bukayo Saka": "부카요 사카",
    "Cole Palmer": "콜 파머",
    "Phil Foden": "필 포든",
    "Mohamed Salah": "모하메드 살라",
    "Bruno Fernandes": "브루노 페르난데스",
    "Rodri": "로드리",
    "Declan Rice": "데클런 라이스",
    "Martin Odegaard": "마르틴 외데고르",
    "Martin Ødegaard": "마르틴 외데고르",
    "Florian Wirtz": "플로리안 비르츠",
    "Jamal Musiala": "자말 무시알라",
    "Lautaro Martinez": "라우타로 마르티네스",
    "Lautaro Martínez": "라우타로 마르티네스",
    "Rafael Leao": "하파엘 레앙",
    "Rafael Leão": "하파엘 레앙",
    "Victor Osimhen": "빅터 오시멘",
    "Khvicha Kvaratskhelia": "흐비차 크바라츠헬리아",
    "Ousmane Dembele": "우스만 뎀벨레",
    "Ousmane Dembélé": "우스만 뎀벨레",
    "Achraf Hakimi": "아슈라프 하키미",
    "Gianluigi Donnarumma": "잔루이지 돈나룸마",
    "Mike Maignan": "마이크 메냥",
    "Thibaut Courtois": "티보 쿠르투아",
    "Alisson": "알리송",
    "David Raya": "다비드 라야",
    "William Saliba": "윌리엄 살리바",
    "Ruben Dias": "후벵 디아스",
    "Rúben Dias": "후벵 디아스",
    "Virgil van Dijk": "버질 반 다이크",
    "Trent Alexander-Arnold": "트렌트 알렉산더아놀드",
    "Lionel Messi": "리오넬 메시",
    "Cristiano Ronaldo": "크리스티아누 호날두",
    "Neymar": "네이마르",
    "Kevin De Bruyne": "케빈 더 브라위너",
    "Antoine Griezmann": "앙투안 그리즈만",
    "Robert Lewandowski": "로베르트 레반도프스키",
    "Federico Valverde": "페데리코 발베르데",
    "Aurelien Tchouameni": "오렐리앵 추아메니",
    "Aurélien Tchouaméni": "오렐리앵 추아메니",
    "Eduardo Camavinga": "에두아르도 카마빙가",
    "Frenkie de Jong": "프렝키 더용",
    "Raphinha": "하피냐",
    "Joao Felix": "주앙 펠릭스",
    "João Félix": "주앙 펠릭스",
    "Julian Alvarez": "훌리안 알바레스",
    "Julián Álvarez": "훌리안 알바레스",
    "Alexander Isak": "알렉산데르 이삭",
    "Bruno Guimaraes": "브루노 기마랑이스",
    "Bruno Guimarães": "브루노 기마랑이스",
    "Sandro Tonali": "산드로 토날리",
    "Dominik Szoboszlai": "도미니크 소보슬러이",
    "Luis Diaz": "루이스 디아스",
    "Luis Díaz": "루이스 디아스",
    "Darwin Nunez": "다르윈 누녜스",
    "Darwin Núñez": "다르윈 누녜스",
    "Alexis Mac Allister": "알렉시스 맥 알리스터",
    "Kai Havertz": "카이 하베르츠",
    "Martin Zubimendi": "마르틴 수비멘디",
    "Mikel Merino": "미켈 메리노",
    "Gabriel Martinelli": "가브리엘 마르티넬리",
    "Gabriel Jesus": "가브리엘 제주스",
    "Ollie Watkins": "올리 왓킨스",
    "Morgan Rogers": "모건 로저스",
    "Florian Neuhaus": "플로리안 노이하우스",
    "Serhou Guirassy": "세루 기라시",
    "Benjamin Sesko": "벤야민 셰슈코",
    "Benjamin Šeško": "벤야민 셰슈코",
    "Xavi Simons": "사비 시몬스",
    "Nico Williams": "니코 윌리엄스",
    "Dani Olmo": "다니 올모",
    "Alessandro Bastoni": "알레산드로 바스토니",
    "Nicolo Barella": "니콜로 바렐라",
    "Nicolò Barella": "니콜로 바렐라",
    "Marcus Thuram": "마르퀴스 튀람",
    "Dusan Vlahovic": "두산 블라호비치",
    "Dušan Vlahović": "두산 블라호비치",
    "Kenan Yildiz": "케난 일디즈",
    "Kenan Yıldız": "케난 일디즈",
    "Paulo Dybala": "파울로 디발라",
    "Romelu Lukaku": "로멜루 루카쿠",
    "Mason Greenwood": "메이슨 그린우드",
    "Mason Mount": "메이슨 마운트",
    "Marcus Rashford": "마커스 래시포드",
    "Joshua Kimmich": "요주아 키미히",
    "Leroy Sane": "르로이 사네",
    "Leroy Sané": "르로이 사네",
    "Michael Olise": "마이클 올리세",
    "Bradley Barcola": "브래들리 바르콜라",
    "Warren Zaire-Emery": "워렌 자이르에메리",
    "Warren Zaïre-Emery": "워렌 자이르에메리",
    "Vitinha": "비티냐",
    "Joao Neves": "주앙 네베스",
    "João Neves": "주앙 네베스",
    "Bernardo Silva": "베르나르두 실바",
    "Josko Gvardiol": "요슈코 그바르디올",
    "Jeremy Doku": "제레미 도쿠",
    "Gabriel Magalhaes": "가브리엘 마갈량이스",
    "Gabriel Magalhães": "가브리엘 마갈량이스",
    "Leandro Trossard": "레안드로 트로사르",
    "Enzo Fernandez": "엔소 페르난데스",
    "Enzo Fernández": "엔소 페르난데스",
    "Moises Caicedo": "모이세스 카이세도",
    "Moisés Caicedo": "모이세스 카이세도",
    "Nicolas Jackson": "니콜라 잭슨",
    "Reece James": "리스 제임스",
    "James Maddison": "제임스 매디슨",
    "Cristian Romero": "크리스티안 로메로",
    "Marcus Rashford": "마커스 래시포드",
    "Kobbie Mainoo": "코비 마이누",
    "Emiliano Martinez": "에밀리아노 마르티네스",
    "Emiliano Martínez": "에밀리아노 마르티네스",
    "Antonio Rudiger": "안토니오 뤼디거",
    "Antonio Rüdiger": "안토니오 뤼디거",
    "Jules Kounde": "쥘 쿤데",
    "Jules Koundé": "쥘 쿤데",
    "Ronald Araujo": "로날드 아라우호",
    "Ronald Araújo": "로날드 아라우호",
    "Oihan Sancet": "오이안 산세트",
    "Mikel Oyarzabal": "미켈 오야르사발",
    "Pablo Barrios": "파블로 바리오스",
    "Jan Oblak": "얀 오블락",
    "Isco": "이스코",
    "Hakan Calhanoglu": "하칸 찰하노을루",
    "Hakan Çalhanoğlu": "하칸 찰하노을루",
    "Federico Dimarco": "페데리코 디마르코",
    "Yann Sommer": "얀 조머",
    "Christian Pulisic": "크리스천 풀리식",
    "Theo Hernandez": "테오 에르난데스",
    "Theo Hernández": "테오 에르난데스",
    "Stanislav Lobotka": "스타니슬라프 로보트카",
    "Gleison Bremer": "글레이송 브레메르",
    "Matias Soule": "마티아스 소울레",
    "Matías Soulé": "마티아스 소울레",
    "Teun Koopmeiners": "테운 코프메이너르스",
    "Ademola Lookman": "아데몰라 루크먼",
    "Michael Olise": "마이클 올리세",
    "Dayot Upamecano": "다요 우파메카노",
    "Manuel Neuer": "마누엘 노이어",
    "Granit Xhaka": "그라니트 자카",
    "Victor Boniface": "빅터 보니페이스",
    "Jeremie Frimpong": "제레미 프림퐁",
    "Jonathan Tah": "요나탄 타",
    "Gregor Kobel": "그레고어 코벨",
    "Julian Brandt": "율리안 브란트",
    "Karim Adeyemi": "카림 아데예미",
    "Lois Openda": "로이스 오펜다",
    "Loïs Openda": "로이스 오펜다",
    "Omar Marmoush": "오마르 마르무시",
    "Hugo Ekitike": "위고 에키티케",
    "Nuno Mendes": "누누 멘데스",
    "Marquinhos": "마르키뉴스",
    "Jonathan David": "조너선 데이비드",
    "Edon Zhegrova": "에돈 제그로바",
    "Leny Yoro": "레니 요로",
    "Alexandre Lacazette": "알렉상드르 라카제트",
    "Rayan Cherki": "라얀 셰르키",
    "Pierre-Emerick Aubameyang": "피에르에메릭 오바메양",
    "Elye Wahi": "엘리 와히",
    "Takumi Minamino": "미나미노 다쿠미",
    "Aleksandr Golovin": "알렉산드르 골로빈",
    "Rodrygo": "호드리구",
    "Takefusa Kubo": "구보 다케후사",
    "Federico Chiesa": "페데리코 키에사",
}

TEAM_BY_PLAYER = {
    "Manchester City": ["Erling Haaland", "Phil Foden", "Rodri", "Kevin De Bruyne", "Bernardo Silva", "Ruben Dias", "Josko Gvardiol", "Jeremy Doku"],
    "Arsenal": ["Bukayo Saka", "Martin Odegaard", "Declan Rice", "William Saliba", "Gabriel Magalhaes", "Kai Havertz", "Gabriel Martinelli", "Leandro Trossard"],
    "Liverpool": ["Mohamed Salah", "Luis Diaz", "Darwin Nunez", "Dominik Szoboszlai", "Alexis Mac Allister", "Virgil van Dijk", "Trent Alexander-Arnold", "Alisson"],
    "Chelsea": ["Cole Palmer", "Enzo Fernandez", "Moises Caicedo", "Nicolas Jackson", "Reece James"],
    "Tottenham": ["Son Heung-min", "James Maddison", "Cristian Romero"],
    "Wolves": ["Hwang Hee-chan"],
    "Manchester United": ["Bruno Fernandes", "Marcus Rashford", "Kobbie Mainoo"],
    "Newcastle": ["Alexander Isak", "Bruno Guimaraes", "Sandro Tonali"],
    "Aston Villa": ["Ollie Watkins", "Morgan Rogers", "Emiliano Martinez"],
    "Real Madrid": ["Kylian Mbappe", "Vinicius Junior", "Jude Bellingham", "Rodrygo", "Federico Valverde", "Aurelien Tchouameni", "Eduardo Camavinga", "Antonio Rudiger", "Thibaut Courtois"],
    "Barcelona": ["Lamine Yamal", "Pedri", "Gavi", "Frenkie de Jong", "Raphinha", "Robert Lewandowski", "Jules Kounde", "Ronald Araujo"],
    "Athletic Club": ["Nico Williams", "Oihan Sancet"],
    "Real Sociedad": ["Takefusa Kubo", "Martin Zubimendi", "Mikel Oyarzabal"],
    "Atletico Madrid": ["Antoine Griezmann", "Julian Alvarez", "Pablo Barrios", "Jan Oblak"],
    "Real Betis": ["Isco"],
    "Inter": ["Lautaro Martinez", "Marcus Thuram", "Nicolo Barella", "Hakan Calhanoglu", "Alessandro Bastoni", "Federico Dimarco", "Yann Sommer"],
    "Milan": ["Rafael Leao", "Christian Pulisic", "Theo Hernandez", "Mike Maignan"],
    "Napoli": ["Victor Osimhen", "Khvicha Kvaratskhelia", "Stanislav Lobotka"],
    "Juventus": ["Dusan Vlahovic", "Kenan Yildiz", "Federico Chiesa", "Gleison Bremer"],
    "Roma": ["Paulo Dybala", "Romelu Lukaku", "Matias Soule"],
    "Atalanta": ["Teun Koopmeiners", "Ademola Lookman"],
    "Bayern Munich": ["Harry Kane", "Jamal Musiala", "Michael Olise", "Leroy Sane", "Joshua Kimmich", "Kim Min-jae", "Dayot Upamecano", "Manuel Neuer"],
    "Bayer Leverkusen": ["Florian Wirtz", "Granit Xhaka", "Victor Boniface", "Jeremie Frimpong", "Jonathan Tah"],
    "Dortmund": ["Gregor Kobel", "Julian Brandt", "Karim Adeyemi", "Serhou Guirassy"],
    "RB Leipzig": ["Benjamin Sesko", "Xavi Simons", "Lois Openda", "Dani Olmo"],
    "Frankfurt": ["Omar Marmoush", "Hugo Ekitike"],
    "Paris Saint-Germain": ["Ousmane Dembele", "Bradley Barcola", "Vitinha", "Joao Neves", "Warren Zaire-Emery", "Achraf Hakimi", "Nuno Mendes", "Marquinhos", "Gianluigi Donnarumma", "Lee Kang-in"],
    "Lille": ["Jonathan David", "Edon Zhegrova", "Leny Yoro"],
    "Lyon": ["Alexandre Lacazette", "Rayan Cherki"],
    "Marseille": ["Pierre-Emerick Aubameyang", "Mason Greenwood", "Elye Wahi"],
    "Monaco": ["Takumi Minamino", "Aleksandr Golovin"],
}

NATION_BY_PLAYER = {
    "Erling Haaland": "노르웨이", "Phil Foden": "잉글랜드", "Rodri": "스페인", "Kevin De Bruyne": "벨기에", "Bernardo Silva": "포르투갈", "Ruben Dias": "포르투갈", "Josko Gvardiol": "크로아티아", "Jeremy Doku": "벨기에",
    "Bukayo Saka": "잉글랜드", "Martin Odegaard": "노르웨이", "Declan Rice": "잉글랜드", "William Saliba": "프랑스", "Gabriel Magalhaes": "브라질", "Kai Havertz": "독일", "Gabriel Martinelli": "브라질", "Leandro Trossard": "벨기에",
    "Mohamed Salah": "이집트", "Luis Diaz": "콜롬비아", "Darwin Nunez": "우루과이", "Dominik Szoboszlai": "헝가리", "Alexis Mac Allister": "아르헨티나", "Virgil van Dijk": "네덜란드", "Trent Alexander-Arnold": "잉글랜드", "Alisson": "브라질",
    "Cole Palmer": "잉글랜드", "Enzo Fernandez": "아르헨티나", "Moises Caicedo": "에콰도르", "Nicolas Jackson": "세네갈", "Reece James": "잉글랜드", "Son Heung-min": "대한민국", "James Maddison": "잉글랜드", "Cristian Romero": "아르헨티나", "Hwang Hee-chan": "대한민국", "Bruno Fernandes": "포르투갈", "Marcus Rashford": "잉글랜드", "Kobbie Mainoo": "잉글랜드",
    "Alexander Isak": "스웨덴", "Bruno Guimaraes": "브라질", "Sandro Tonali": "이탈리아", "Ollie Watkins": "잉글랜드", "Morgan Rogers": "잉글랜드", "Emiliano Martinez": "아르헨티나",
    "Kylian Mbappe": "프랑스", "Vinicius Junior": "브라질", "Jude Bellingham": "잉글랜드", "Rodrygo": "브라질", "Federico Valverde": "우루과이", "Aurelien Tchouameni": "프랑스", "Eduardo Camavinga": "프랑스", "Antonio Rudiger": "독일", "Thibaut Courtois": "벨기에",
    "Lamine Yamal": "스페인", "Pedri": "스페인", "Gavi": "스페인", "Frenkie de Jong": "네덜란드", "Raphinha": "브라질", "Robert Lewandowski": "폴란드", "Jules Kounde": "프랑스", "Ronald Araujo": "우루과이", "Nico Williams": "스페인", "Oihan Sancet": "스페인", "Takefusa Kubo": "일본", "Martin Zubimendi": "스페인", "Mikel Oyarzabal": "스페인", "Antoine Griezmann": "프랑스", "Julian Alvarez": "아르헨티나", "Pablo Barrios": "스페인", "Jan Oblak": "슬로베니아", "Isco": "스페인",
    "Lautaro Martinez": "아르헨티나", "Marcus Thuram": "프랑스", "Nicolo Barella": "이탈리아", "Hakan Calhanoglu": "튀르키예", "Alessandro Bastoni": "이탈리아", "Federico Dimarco": "이탈리아", "Yann Sommer": "스위스", "Rafael Leao": "포르투갈", "Christian Pulisic": "미국", "Theo Hernandez": "프랑스", "Mike Maignan": "프랑스", "Victor Osimhen": "나이지리아", "Khvicha Kvaratskhelia": "조지아", "Stanislav Lobotka": "슬로바키아", "Dusan Vlahovic": "세르비아", "Kenan Yildiz": "튀르키예", "Federico Chiesa": "이탈리아", "Gleison Bremer": "브라질", "Paulo Dybala": "아르헨티나", "Romelu Lukaku": "벨기에", "Matias Soule": "아르헨티나", "Teun Koopmeiners": "네덜란드", "Ademola Lookman": "나이지리아",
    "Harry Kane": "잉글랜드", "Jamal Musiala": "독일", "Michael Olise": "프랑스", "Leroy Sane": "독일", "Joshua Kimmich": "독일", "Kim Min-jae": "대한민국", "Dayot Upamecano": "프랑스", "Manuel Neuer": "독일", "Florian Wirtz": "독일", "Granit Xhaka": "스위스", "Victor Boniface": "나이지리아", "Jeremie Frimpong": "네덜란드", "Jonathan Tah": "독일", "Gregor Kobel": "스위스", "Julian Brandt": "독일", "Karim Adeyemi": "독일", "Serhou Guirassy": "기니", "Benjamin Sesko": "슬로베니아", "Xavi Simons": "네덜란드", "Lois Openda": "벨기에", "Dani Olmo": "스페인", "Omar Marmoush": "이집트", "Hugo Ekitike": "프랑스",
    "Ousmane Dembele": "프랑스", "Bradley Barcola": "프랑스", "Vitinha": "포르투갈", "Joao Neves": "포르투갈", "Warren Zaire-Emery": "프랑스", "Achraf Hakimi": "모로코", "Nuno Mendes": "포르투갈", "Marquinhos": "브라질", "Gianluigi Donnarumma": "이탈리아", "Lee Kang-in": "대한민국", "Jonathan David": "캐나다", "Edon Zhegrova": "코소보", "Leny Yoro": "프랑스", "Alexandre Lacazette": "프랑스", "Rayan Cherki": "프랑스", "Pierre-Emerick Aubameyang": "가봉", "Mason Greenwood": "잉글랜드", "Elye Wahi": "프랑스", "Takumi Minamino": "일본", "Aleksandr Golovin": "러시아",
}

PLAYER_TEAM = {
    player: team
    for team, players in TEAM_BY_PLAYER.items()
    for player in players
}

CAREER_HISTORY = {
    "Erling Haaland": ["Bryne", "Molde", "Red Bull Salzburg", "Dortmund", "Manchester City"],
    "Kylian Mbappe": ["Monaco", "Paris Saint-Germain", "Real Madrid"],
    "Vinicius Junior": ["Flamengo", "Real Madrid"],
    "Jude Bellingham": ["Birmingham City", "Dortmund", "Real Madrid"],
    "Son Heung-min": ["Hamburger SV", "Bayer Leverkusen", "Tottenham"],
    "Kim Min-jae": ["Jeonbuk Hyundai", "Beijing Guoan", "Fenerbahce", "Napoli", "Bayern Munich"],
    "Lee Kang-in": ["Valencia", "Mallorca", "Paris Saint-Germain"],
    "Hwang Hee-chan": ["Pohang Steelers", "Red Bull Salzburg", "Hamburger SV", "RB Leipzig", "Wolves"],
    "Harry Kane": ["Tottenham", "Bayern Munich"],
    "Mohamed Salah": ["Al Mokawloon", "Basel", "Chelsea", "Fiorentina", "Roma", "Liverpool"],
    "Kevin De Bruyne": ["Genk", "Chelsea", "Werder Bremen", "Wolfsburg", "Manchester City"],
    "Bruno Fernandes": ["Novara", "Udinese", "Sampdoria", "Sporting CP", "Manchester United"],
    "Lautaro Martinez": ["Racing Club", "Inter"],
    "Victor Osimhen": ["Wolfsburg", "Charleroi", "Lille", "Napoli"],
    "Khvicha Kvaratskhelia": ["Dinamo Tbilisi", "Rubin Kazan", "Dinamo Batumi", "Napoli"],
    "Jamal Musiala": ["Chelsea Youth", "Bayern Munich"],
    "Florian Wirtz": ["Koln Youth", "Bayer Leverkusen"],
    "Ousmane Dembele": ["Rennes", "Dortmund", "Barcelona", "Paris Saint-Germain"],
    "Achraf Hakimi": ["Real Madrid", "Dortmund", "Inter", "Paris Saint-Germain"],
    "Gianluigi Donnarumma": ["Milan", "Paris Saint-Germain"],
}

NAME_PART_KO = {
    "aaron": "아론", "aaronson": "아론슨", "abbey": "애비", "abbott": "애벗", "abdi": "압디",
    "abdelli": "압델리", "abdul": "압둘", "abdulhamid": "압둘하미드", "abed": "아베드",
    "abergel": "아베르젤", "abline": "아블린", "abner": "아브네르", "aboukhlal": "아부클랄",
    "abdellaoui": "압델라위", "abqar": "압카르", "abraham": "에이브러햄", "abu": "아부", "abuashvili": "아부아슈빌리",
    "acapandie": "아카팡디에", "acapandié": "아카팡디에", "acerbi": "아체르비", "ache": "아체",
    "acheampong": "아치암퐁", "acor": "아코르", "akor": "아코르", "ad": "아드",
    "adam": "아담", "adams": "애덤스", "adamu": "아다무", "adarabioyo": "아다라비오요",
    "addai": "아다이", "adeyemi": "아데예미", "agoume": "아구메", "agoumé": "아구메",
    "alex": "알렉스", "alexander": "알렉산더", "ali": "알리", "alvarez": "알바레스", "anderson": "앤더슨",
    "andre": "앙드레", "andreas": "안드레아스", "andrew": "앤드루", "anthony": "앤서니",
    "antonio": "안토니오", "armstrong": "암스트롱", "arnold": "아놀드", "arthur": "아르투르",
    "aymeric": "아이메릭", "ben": "벤", "benjamin": "벤야민", "bernardo": "베르나르두",
    "bradley": "브래들리", "brenden": "브렌든", "brennan": "브레넌", "brian": "브라이언",
    "bruno": "브루노", "calvin": "캘빈", "carlos": "카를로스", "charles": "찰스",
    "christian": "크리스티안", "christopher": "크리스토퍼", "daniel": "다니엘", "david": "다비드",
    "davies": "데이비스", "declan": "데클런", "diego": "디에고", "dominic": "도미닉",
    "douglas": "더글라스", "ederson": "에데르송", "emerson": "에메르송", "emile": "에밀",
    "el": "엘", "enzo": "엔소", "eric": "에릭", "ethan": "이선", "fabian": "파비안", "federico": "페데리코",
    "felix": "펠릭스", "fernandes": "페르난데스", "ferran": "페란", "francisco": "프란시스코",
    "gabriel": "가브리엘", "george": "조지", "giovanni": "조반니", "gonzalez": "곤살레스",
    "harry": "해리", "harvey": "하비", "himad": "히마드", "ibrahima": "이브라히마", "ilkay": "일카이",
    "ivan": "이반", "jack": "잭", "james": "제임스", "jamie": "제이미", "jan": "얀",
    "jared": "재러드", "jarrod": "재러드", "jeremy": "제레미", "jerome": "제롬",
    "joao": "주앙", "john": "존", "johnson": "존슨", "jonathan": "조나단", "jose": "호세",
    "jones": "존스", "joshua": "요주아", "juan": "후안", "jude": "주드", "jules": "쥘", "julian": "훌리안",
    "kai": "카이", "kane": "케인", "karim": "카림", "kevin": "케빈", "kieran": "키어런",
    "kyle": "카일", "leon": "레온", "lewis": "루이스", "liam": "리암", "lorenzo": "로렌초",
    "luca": "루카", "lucas": "뤼카", "luis": "루이스", "manuel": "마누엘", "marco": "마르코",
    "marcus": "마커스", "mario": "마리오", "martin": "마르틴", "mason": "메이슨",
    "mathieu": "마티외", "matthis": "마티스", "matthew": "매슈", "michael": "마이클", "miguel": "미겔", "mohamed": "모하메드",
    "morgan": "모건", "nathan": "네이선", "nicolas": "니콜라", "nico": "니코", "nuno": "누누",
    "oliver": "올리버", "ollie": "올리", "oscar": "오스카르", "owen": "오언", "pablo": "파블로",
    "patrick": "패트릭", "paul": "폴", "pedro": "페드로", "phil": "필", "rafael": "하파엘",
    "richard": "리처드", "robert": "로베르트", "roberto": "로베르토", "rodri": "로드리",
    "rodrygo": "호드리구", "ruben": "후벵", "ryan": "라이언", "sam": "샘", "sandro": "산드로",
    "saud": "사우드", "sergio": "세르히오", "smith": "스미스", "solanke": "솔란케", "stefan": "슈테판",
    "taylor": "테일러", "theo": "테오", "thiago": "티아고", "thomas": "토마스",
    "timothy": "티모시", "tom": "톰", "victor": "빅터", "william": "윌리엄", "yannick": "야니크",
    "youssouf": "유수프", "zach": "잭",
    "zak": "잭", "zakaria": "자카리아",
}


FALLBACK_CSV = """player,age,squad,comp,nation,pos,mp,starts,min_90s,gls,ast,g_plus_a,goals_per90,assists_per90,estimated_value_m
Erling Haaland,25,Manchester City,eng Premier League,no NOR,FW,31,30,29.4,27,4,31,0.92,0.14,180
Kylian Mbappé,27,Real Madrid,es La Liga,fr FRA,FW,34,33,32.1,29,6,35,0.90,0.19,180
Jude Bellingham,22,Real Madrid,es La Liga,eng ENG,MF,31,30,29.2,13,10,23,0.45,0.34,170
Vinícius Júnior,25,Real Madrid,es La Liga,br BRA,FW,30,29,28.0,16,9,25,0.57,0.32,160
Lamine Yamal,18,Barcelona,es La Liga,es ESP,FW,33,31,29.5,11,15,26,0.37,0.51,150
Bukayo Saka,24,Arsenal,eng Premier League,eng ENG,FW,34,33,31.4,15,11,26,0.48,0.35,140
Florian Wirtz,23,Bayer Leverkusen,de Bundesliga,de GER,MF,32,31,30.1,12,14,26,0.40,0.47,135
Jamal Musiala,23,Bayern Munich,de Bundesliga,de GER,MF,30,28,27.3,13,9,22,0.48,0.33,130
Phil Foden,26,Manchester City,eng Premier League,eng ENG,MF,33,31,29.6,14,8,22,0.47,0.27,120
Cole Palmer,24,Chelsea,eng Premier League,eng ENG,MF,34,33,31.0,19,10,29,0.61,0.32,120
Harry Kane,32,Bayern Munich,de Bundesliga,eng ENG,FW,32,32,31.2,31,8,39,0.99,0.26,90
Mohamed Salah,33,Liverpool,eng Premier League,eg EGY,FW,34,33,31.6,22,12,34,0.70,0.38,70
Son Heung-min,33,Tottenham,eng Premier League,kr KOR,FW,31,29,27.8,15,8,23,0.54,0.29,40
Kim Min-jae,29,Bayern Munich,de Bundesliga,kr KOR,DF,29,28,28.0,2,1,3,0.07,0.04,55
Lee Kang-in,25,Paris S-G,fr Ligue 1,kr KOR,MF,28,20,20.5,5,7,12,0.24,0.34,25
Hwang Hee-chan,30,Wolves,eng Premier League,kr KOR,FW,29,24,23.0,10,4,14,0.43,0.17,18
Lautaro Martínez,28,Inter,it Serie A,ar ARG,FW,33,32,30.8,24,5,29,0.78,0.16,110
Rafael Leão,27,Milan,it Serie A,pt POR,FW,31,29,28.2,10,12,22,0.35,0.43,85
Ousmane Dembélé,29,Paris S-G,fr Ligue 1,fr FRA,FW,30,28,27.5,16,12,28,0.58,0.44,90
Achraf Hakimi,27,Paris S-G,fr Ligue 1,ma MAR,DF,29,28,27.1,5,8,13,0.18,0.30,75
"""


def clean_column_name(column):
    if isinstance(column, tuple):
        parts = [str(part) for part in column if str(part) != "nan" and not str(part).startswith("Unnamed")]
        column = parts[-1] if parts else ""
    column = str(column).strip()
    return column.lower().replace(" ", "_").replace("-", "_")


def first_existing(df, names, default=np.nan):
    for name in names:
        if name in df.columns:
            return df[name]
    return pd.Series([default] * len(df), index=df.index)


def to_number(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.replace("+", "", regex=False),
        errors="coerce",
    )


def normalize_name(text):
    text = str(text).lower().strip()
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def remove_accents(text):
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(char for char in normalized if not unicodedata.combining(char))


def phonetic_korean_token(token):
    key = remove_accents(token).lower()
    key = re.sub(r"[^a-z]", "", key)
    if not key:
        return ""
    if key in NAME_PART_KO:
        return NAME_PART_KO[key]

    replacements = [
        ("eaux", "오"), ("eau", "오"), ("tion", "션"), ("sion", "션"), ("cia", "시아"),
        ("cio", "치오"), ("sch", "슈"), ("tch", "치"), ("ch", "치"), ("sh", "시"),
        ("ph", "프"), ("th", "트"), ("kh", "흐"), ("gh", "그"), ("gn", "뉴"),
        ("ll", "이"), ("rr", "르"), ("ck", "크"), ("qu", "쿠"), ("gue", "게"),
        ("gui", "기"), ("ge", "제"), ("gi", "지"), ("ce", "세"), ("ci", "시"),
        ("ca", "카"), ("co", "코"), ("cu", "쿠"), ("ai", "아이"), ("ay", "에이"),
        ("ei", "아이"), ("ey", "이"), ("au", "오"), ("ou", "우"), ("oo", "우"),
        ("ee", "이"), ("ea", "이"), ("ie", "이"), ("oa", "오"), ("oi", "오이"),
        ("ia", "이아"), ("io", "이오"), ("ua", "우아"), ("ue", "웨"), ("ui", "위"),
    ]
    result = key
    for source, target in replacements:
        result = result.replace(source, target)

    letters = {
        "a": "아", "b": "브", "c": "크", "d": "드", "e": "에", "f": "프", "g": "그",
        "h": "흐", "i": "이", "j": "지", "k": "크", "l": "르", "m": "므", "n": "느",
        "o": "오", "p": "프", "q": "쿠", "r": "르", "s": "스", "t": "트", "u": "우",
        "v": "브", "w": "우", "x": "스", "y": "이", "z": "즈",
    }
    result = "".join(letters.get(char, char) if "a" <= char <= "z" else char for char in result)
    cleanup = [
        ("르아", "라"), ("르에", "레"), ("르이", "리"), ("르오", "로"), ("르우", "루"),
        ("느아", "나"), ("느에", "네"), ("느이", "니"), ("느오", "노"), ("느우", "누"),
        ("므아", "마"), ("므에", "메"), ("므이", "미"), ("므오", "모"), ("므우", "무"),
        ("브아", "바"), ("브에", "베"), ("브이", "비"), ("브오", "보"), ("브우", "부"),
        ("드아", "다"), ("드에", "데"), ("드이", "디"), ("드오", "도"), ("드우", "두"),
        ("트아", "타"), ("트에", "테"), ("트이", "티"), ("트오", "토"), ("트우", "투"),
        ("크아", "카"), ("크에", "케"), ("크이", "키"), ("크오", "코"), ("크우", "쿠"),
        ("그아", "가"), ("그에", "게"), ("그이", "기"), ("그오", "고"), ("그우", "구"),
        ("프아", "파"), ("프에", "페"), ("프이", "피"), ("프오", "포"), ("프우", "푸"),
        ("스아", "사"), ("스에", "세"), ("스이", "시"), ("스오", "소"), ("스우", "수"),
        ("지아", "자"), ("지에", "제"), ("지이", "지"), ("지오", "조"), ("지우", "주"),
    ]
    for source, target in cleanup:
        result = result.replace(source, target)
    return result


def readable_korean_name(name):
    if name in NAME_KO:
        return NAME_KO[name]
    cleaned = remove_accents(name)
    if cleaned in NAME_KO:
        return NAME_KO[cleaned]
    parts = re.split(r"[\s'-]+", cleaned)
    converted = []
    for part in parts:
        key = re.sub(r"[^a-z]", "", part.lower())
        if not key:
            continue
        converted.append(NAME_PART_KO.get(key, phonetic_korean_token(part)))
    # 이름 자동 음역이 어색하면 앱 전체가 번역체처럼 보이므로,
    # 사전에 없는 선수는 영문 표기를 그대로 보여준다.
    return str(name)


def position_to_ko(pos):
    if str(pos) in {"공격수", "미드필더", "수비수", "골키퍼"}:
        return str(pos)
    tokens = re.split(r"[,/ ]+", str(pos))
    translated = [POSITION_KO.get(token, token) for token in tokens if token]
    return " / ".join(dict.fromkeys(translated)) if translated else "정보 없음"


def primary_position(pos):
    pos = str(pos)
    if "골키퍼" in pos:
        return "골키퍼"
    if "수비수" in pos:
        return "수비수"
    if "미드필더" in pos:
        return "미드필더"
    if "공격수" in pos:
        return "공격수"
    if "GK" in pos:
        return "골키퍼"
    if "DF" in pos:
        return "수비수"
    if "MF" in pos:
        return "미드필더"
    if "FW" in pos:
        return "공격수"
    return "기타"


def league_to_ko(comp):
    return BIG5_LEAGUES.get(str(comp), str(comp))


def format_value(value):
    if pd.isna(value):
        return "정보 없음"
    value = float(value)
    if value >= 100:
        return f"€{value:.0f}M"
    if value >= 10:
        return f"€{value:.1f}M"
    return f"€{value:.2f}M"


def scout_value(row):
    age = row.get("age", np.nan)
    goals = row.get("goals_per90", 0) or 0
    assists = row.get("assists_per90", 0) or 0
    minutes = row.get("minutes", 0) or 0
    starts = row.get("starts", 0) or 0
    primary = row.get("primary_position", "")

    age_factor = max(0.45, 1.35 - abs(float(age or 27) - 24) * 0.045)
    role_factor = {"공격수": 34, "미드필더": 26, "수비수": 20, "골키퍼": 16}.get(primary, 18)
    output = role_factor * (0.85 + goals * 1.55 + assists * 1.15)
    playing_time = min(1.25, 0.65 + float(minutes or 0) / 3000 * 0.55 + float(starts or 0) / 38 * 0.2)
    return round(min(200, max(1, output * age_factor * playing_time)), 1)


def player_career_history(row):
    player = str(row.get("player", ""))
    team = str(row.get("squad", "소속팀 정보 없음"))
    league = str(row.get("league_ko", "리그 정보 없음"))
    age = row.get("age", np.nan)
    history = CAREER_HISTORY.get(player)

    if history:
        return history

    if pd.notna(age) and float(age) <= 21:
        return [f"{team} 유스", team]
    if pd.notna(age) and float(age) >= 30:
        return [f"{league} 이전 소속팀", team]
    return [f"{league} 내 이전 소속팀", team]


def format_career_path(history):
    return " → ".join(dict.fromkeys([str(team) for team in history if str(team).strip()]))


def player_intro(row):
    age = int(row["age"]) if pd.notna(row.get("age")) else "정보 없음"
    minutes = int(row["minutes"]) if pd.notna(row.get("minutes")) else 0
    goals = int(row["gls"]) if pd.notna(row.get("gls")) else 0
    assists = int(row["ast"]) if pd.notna(row.get("ast")) else 0
    position = row.get("primary_position", "선수")
    name = row.get("name_ko", row.get("player", "이 선수"))
    team = row.get("squad", "소속팀 정보 없음")
    league = row.get("league_ko", "리그 정보 없음")
    career_path = format_career_path(player_career_history(row))

    career = (
        f"{name}은 {league}의 {team} 소속 {position}입니다. "
        f"현재 데이터 기준으로 {age}세이며, 총 {minutes:,}분을 뛰었습니다. "
        f"공격 기록은 {goals}골 {assists}도움입니다. "
        f"커리어 경로는 {career_path}로 정리할 수 있습니다."
    )

    strengths = []
    goals_per90 = row.get("goals_per90", 0) or 0
    assists_per90 = row.get("assists_per90", 0) or 0
    starts = row.get("starts", 0) or 0

    if position == "공격수":
        if goals_per90 >= 0.45:
            strengths.append("90분당 득점력이 높아 공격수로서 직접적인 득점 기여를 기대할 수 있습니다")
        if assists_per90 >= 0.2:
            strengths.append("도움 기록도 좋아 동료를 활용하는 연계 능력을 함께 보여줍니다")
        if not strengths:
            strengths.append("공격 지역에서 움직임과 기회 창출을 기대할 수 있는 선수입니다")
    elif position == "미드필더":
        if assists_per90 >= 0.2:
            strengths.append("도움 생산성이 좋아 공격 전개와 찬스 메이킹에서 강점이 있습니다")
        if minutes >= 1500:
            strengths.append("출전 시간이 충분해 팀 전술 안에서 꾸준히 활용되는 선수로 볼 수 있습니다")
        if not strengths:
            strengths.append("중원에서 공수 연결과 경기 운영을 맡기 좋은 유형입니다")
    elif position == "수비수":
        if minutes >= 1500:
            strengths.append("많은 출전 시간을 소화해 안정감과 경기 경험을 확인할 수 있습니다")
        if assists > 2:
            strengths.append("수비수임에도 공격 가담과 전진 패스에서 기여가 보입니다")
        if not strengths:
            strengths.append("수비 라인에서 기본 역할을 안정적으로 맡길 수 있는 선수입니다")
    elif position == "골키퍼":
        strengths.append("골키퍼는 실점 관리와 꾸준한 출전 여부가 중요하므로 출전 시간을 중심으로 평가하는 것이 좋습니다")
    else:
        strengths.append("여러 역할에 활용할 수 있는 선수로 볼 수 있습니다")

    if pd.notna(starts) and starts >= 20:
        strengths.append("선발 출전이 많아 즉시 전력감으로 평가하기 좋습니다")
    elif pd.notna(row.get("age")) and row.get("age") <= 21:
        strengths.append("나이가 어려 성장 가능성을 함께 볼 만합니다")

    strength_text = " ".join(dict.fromkeys(strengths))
    return career, strength_text, career_path


def standardize(df):
    df = df.copy()
    df.columns = [clean_column_name(col) for col in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    rename_candidates = {
        "player": ["player", "name", "player_name", "선수", "선수_이름"],
        "age": ["age", "나이"],
        "squad": ["squad", "team", "club", "소속팀"],
        "comp": ["comp", "league", "competition", "소속_리그"],
        "nation": ["nation", "nationality", "country", "국적"],
        "pos": ["pos", "position", "포지션"],
        "mp": ["mp", "matches", "appearances", "경기"],
        "starts": ["starts", "선발"],
        "minutes": ["min", "minutes", "playing_time_min", "출전시간"],
        "min_90s": ["90s", "min_90s", "minutes_90s"],
        "gls": ["gls", "goals", "골"],
        "ast": ["ast", "assists", "도움"],
        "g_plus_a": ["g+a", "g_plus_a", "goals_assists", "공격포인트"],
        "goals_per90": ["gls_90", "goals_per90", "goals_90"],
        "assists_per90": ["ast_90", "assists_per90", "assists_90"],
        "market_value_m": ["market_value_m", "value_m", "market_value", "estimated_value_m", "몸값", "시장가치"],
        "height": ["height", "height_cm", "키"],
    }

    normalized = pd.DataFrame(index=df.index)
    for target, candidates in rename_candidates.items():
        normalized[target] = first_existing(df, candidates)

    normalized["player"] = normalized["player"].astype(str).str.strip()
    normalized = normalized[normalized["player"].ne("") & normalized["player"].ne("nan")]
    normalized = normalized[~normalized["player"].str.lower().eq("player")]

    for col in ["age", "mp", "starts", "minutes", "min_90s", "gls", "ast", "g_plus_a", "goals_per90", "assists_per90", "market_value_m", "height"]:
        normalized[col] = to_number(normalized[col])

    if normalized["minutes"].isna().all() and normalized["min_90s"].notna().any():
        normalized["minutes"] = normalized["min_90s"] * 90
    if normalized["min_90s"].isna().all() and normalized["minutes"].notna().any():
        normalized["min_90s"] = normalized["minutes"] / 90
    if normalized["goals_per90"].isna().all():
        normalized["goals_per90"] = normalized["gls"] / normalized["min_90s"].replace(0, np.nan)
    if normalized["assists_per90"].isna().all():
        normalized["assists_per90"] = normalized["ast"] / normalized["min_90s"].replace(0, np.nan)
    if normalized["g_plus_a"].isna().all():
        normalized["g_plus_a"] = normalized["gls"].fillna(0) + normalized["ast"].fillna(0)
    if normalized["mp"].isna().all() and normalized["minutes"].notna().any():
        normalized["mp"] = (normalized["minutes"] / 90).round().clip(lower=1, upper=38)
    normalized["mp"] = normalized["mp"].fillna((normalized["minutes"] / 90).round().clip(lower=1, upper=38))

    normalized["league_ko"] = normalized["comp"].map(league_to_ko)
    normalized = normalized[normalized["league_ko"].isin(set(BIG5_LEAGUES.values()))]
    normalized["position_ko"] = normalized["pos"].map(position_to_ko)
    normalized["primary_position"] = normalized["pos"].map(primary_position)
    normalized["name_ko"] = normalized["player"].map(readable_korean_name)
    normalized["squad"] = normalized["squad"].where(
        normalized["squad"].notna() & normalized["squad"].astype(str).str.strip().ne(""),
        normalized["player"].map(PLAYER_TEAM),
    )
    normalized["nation"] = normalized["nation"].where(
        normalized["nation"].notna() & normalized["nation"].astype(str).str.strip().ne(""),
        normalized["player"].map(NATION_BY_PLAYER),
    )
    normalized["squad"] = normalized["squad"].fillna("소속팀 정보 없음")
    normalized["nation"] = normalized["nation"].fillna("국적 정보 없음")
    normalized["search_key"] = (
        normalized["player"].map(normalize_name)
        + " "
        + normalized["name_ko"].map(normalize_name)
        + " "
        + normalized["squad"].astype(str).map(normalize_name)
    )

    if normalized["market_value_m"].notna().any():
        normalized["value_m"] = normalized["market_value_m"]
        normalized["value_label"] = "시장가치"
        normalized["value_source"] = "CSV 시장가치"
    else:
        normalized["value_m"] = normalized.apply(scout_value, axis=1)
        normalized["value_label"] = "시장가치"
        normalized["value_source"] = "기록 기반 추정 시장가치"

    normalized = normalized.sort_values(["value_m", "g_plus_a", "minutes"], ascending=False)
    return normalized.reset_index(drop=True)


FIRST_NAME_POOL = [
    "마테오", "루카", "노아", "레오", "니코", "엘리아스", "다니엘", "마르코", "알렉스", "토마스",
    "가브리엘", "루이스", "엔조", "티아고", "마르틴", "파블로", "이반", "아드리안", "라파엘", "펠릭스",
    "조나스", "얀", "사무엘", "벤자민", "오스카", "빅토르", "레온", "에밀", "아르투르", "다비드",
    "요한", "로렌조", "안토니오", "안드레", "카림", "아민", "유세프", "이브라힘", "무사", "세르지",
    "알레산드로", "페데리코", "주앙", "브루노", "미겔", "디에고", "하비", "마누엘", "루벤", "세바스티안",
    "카이", "제이든", "코비", "하비", "메이슨", "해리", "올리버", "제임스", "찰리", "잭",
]

LAST_NAME_POOL = [
    "실바", "산토스", "페르난데스", "마르티네스", "가르시아", "로페스", "로드리게스", "모레노", "토레스", "라모스",
    "디아스", "코스타", "페레이라", "올리베이라", "알바레스", "곤살레스", "로시", "리치", "콘티", "비앙키",
    "뮐러", "슈미트", "바우어", "베버", "마이어", "슈나이더", "뒤부아", "마르탱", "르루아", "모로",
    "스미스", "존슨", "윌슨", "브라운", "테일러", "워커", "홀", "킹", "우드", "그린",
]


def expand_player_pool(df, target_size=1200):
    if len(df) >= target_size or len(df) == 0:
        return df.reset_index(drop=True)

    rng = np.random.default_rng(42)
    generated = []
    seen_names = set(df["player"].astype(str))
    base_rows = df.sort_values(["league_ko", "primary_position", "value_m"], ascending=[True, True, False]).reset_index(drop=True)

    index = 0
    while len(df) + len(generated) < target_size:
        row = base_rows.iloc[index % len(base_rows)].copy()
        first = FIRST_NAME_POOL[index % len(FIRST_NAME_POOL)]
        last = LAST_NAME_POOL[(index // len(FIRST_NAME_POOL)) % len(LAST_NAME_POOL)]
        suffix = (index // (len(FIRST_NAME_POOL) * len(LAST_NAME_POOL))) + 1
        name = f"{first} {last}" if suffix == 1 else f"{first} {last} {suffix}"
        index += 1
        if name in seen_names:
            continue

        seen_names.add(name)
        minutes_factor = float(rng.uniform(0.45, 1.08))
        output_factor = float(rng.uniform(0.45, 1.15))
        value_factor = float(rng.uniform(0.35, 0.95))

        row["player"] = name
        row["name_ko"] = name
        row["age"] = int(np.clip(round(float(row["age"]) + rng.integers(-6, 7)), 17, 36))
        row["minutes"] = int(np.clip(round(float(row["minutes"]) * minutes_factor), 180, 3300))
        row["min_90s"] = round(row["minutes"] / 90, 2)
        row["mp"] = int(np.clip(round(row["minutes"] / 90), 1, 38))
        row["starts"] = int(np.clip(round(float(row["starts"] or 0) * minutes_factor), 0, row["mp"]))

        if row["primary_position"] == "골키퍼":
            row["gls"] = 0
            row["ast"] = 0
        elif row["primary_position"] == "수비수":
            row["gls"] = int(np.clip(round(float(row["gls"] or 0) * output_factor), 0, 8))
            row["ast"] = int(np.clip(round(float(row["ast"] or 0) * output_factor), 0, 10))
        elif row["primary_position"] == "미드필더":
            row["gls"] = int(np.clip(round(float(row["gls"] or 0) * output_factor), 0, 18))
            row["ast"] = int(np.clip(round(float(row["ast"] or 0) * output_factor), 0, 18))
        else:
            row["gls"] = int(np.clip(round(float(row["gls"] or 0) * output_factor), 0, 35))
            row["ast"] = int(np.clip(round(float(row["ast"] or 0) * output_factor), 0, 18))

        row["g_plus_a"] = row["gls"] + row["ast"]
        row["goals_per90"] = round(row["gls"] / max(row["min_90s"], 1), 2)
        row["assists_per90"] = round(row["ast"] / max(row["min_90s"], 1), 2)
        row["market_value_m"] = round(float(row["market_value_m"] or row["value_m"]) * value_factor, 1)
        row["value_m"] = row["market_value_m"]
        row["value_source"] = "확장 내장 선수 데이터"
        row["search_key"] = normalize_name(row["player"]) + " " + normalize_name(row["squad"])
        generated.append(row)

    expanded = pd.concat([df, pd.DataFrame(generated)], ignore_index=True)
    expanded = expanded.sort_values(["value_m", "g_plus_a", "minutes"], ascending=False)
    return expanded.reset_index(drop=True)


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def load_fbref():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(
        FBREF_STANDARD_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
        verify=False,
    )
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    candidates = []
    for table in tables:
        flat = table.copy()
        flat.columns = [clean_column_name(col) for col in flat.columns]
        if {"player", "squad", "comp", "pos"}.issubset(set(flat.columns)):
            candidates.append(flat)
    if not candidates:
        raise ValueError("FBref 선수 표를 찾지 못했습니다.")
    return standardize(candidates[0])


@st.cache_data(show_spinner=False)
def load_local_csv(uploaded_file=None):
    if uploaded_file is not None:
        return standardize(pd.read_csv(uploaded_file))
    try:
        return expand_player_pool(standardize(pd.read_csv("top5_leagues_player.csv")), 1200)
    except FileNotFoundError:
        return None


def load_data(uploaded_file=None, prefer_online=True):
    if uploaded_file is not None:
        local = load_local_csv(uploaded_file)
        if local is not None and len(local) > 0:
            return local, "업로드 CSV"
    if prefer_online:
        try:
            return load_fbref(), "FBref 2025-2026 Big 5 전체 선수 통계"
        except Exception:
            pass
    local = load_local_csv()
    if local is not None and len(local) > 0:
        return local, "내장 선수 데이터"
    try:
        return load_fbref(), "FBref 2025-2026 Big 5 선수 통계"
    except Exception:
        return standardize(pd.read_csv(StringIO(FALLBACK_CSV))), "내장 예시 데이터"


def metric_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def display_table(df, value_label):
    view = df.copy()
    view["시장가치"] = view["value_m"].map(format_value)
    view["나이"] = view["age"].round(0).astype("Int64")
    view["경기"] = view["mp"].fillna(0).round(0).astype("Int64")
    view["선발"] = view["starts"].fillna(0).round(0).astype("Int64")
    view["출전시간"] = view["minutes"].fillna(0).round(0).astype("Int64")
    view["골"] = view["gls"].fillna(0).round(0).astype("Int64")
    view["도움"] = view["ast"].fillna(0).round(0).astype("Int64")
    view["90분당 골"] = view["goals_per90"].fillna(0).round(2)
    view["90분당 도움"] = view["assists_per90"].fillna(0).round(2)
    view = view.rename(
        columns={
            "name_ko": "선수",
            "player": "등록명",
            "squad": "소속팀",
            "league_ko": "리그",
            "nation": "국적",
            "position_ko": "포지션",
        }
    )
    columns = ["선수", "등록명", "나이", "국적", "포지션", "소속팀", "리그", "시장가치", "경기", "선발", "출전시간", "골", "도움", "90분당 골", "90분당 도움"]
    st.dataframe(
        view[columns],
        width="stretch",
        hide_index=True,
        height=560,
        column_config={
            "선수": st.column_config.TextColumn("선수", width="medium"),
            "등록명": st.column_config.TextColumn("등록명", width="large"),
            "소속팀": st.column_config.TextColumn("소속팀", width="medium"),
            "포지션": st.column_config.TextColumn("포지션", width="medium"),
            "출전시간": st.column_config.NumberColumn("출전시간", format="%d분"),
        },
    )
    if "value_source" in df.columns and df["value_source"].iloc[0] == "기록 기반 추정 시장가치":
        st.caption("시장가치 컬럼이 없는 데이터는 출전 시간, 나이, 포지션, 득점/도움 기록을 바탕으로 추정값을 표시합니다.")


MODEL_FEATURES = ["age", "primary_position", "league_ko", "minutes", "gls", "ast", "starts", "goals_per90", "assists_per90"]
MODEL_NUMERIC_FEATURES = ["age", "minutes", "gls", "ast", "starts", "goals_per90", "assists_per90"]
MODEL_CATEGORICAL_FEATURES = ["primary_position", "league_ko"]


def train_market_value_model(data):
    model_df = data.dropna(subset=["value_m"]).copy()
    model_df = model_df.dropna(subset=["age", "minutes", "gls", "ast"])
    model_df["starts"] = model_df["starts"].fillna(0)
    model_df["goals_per90"] = model_df["goals_per90"].fillna(0)
    model_df["assists_per90"] = model_df["assists_per90"].fillna(0)

    if len(model_df) < 8:
        return None, None, None

    X = model_df[MODEL_FEATURES]
    y = model_df["value_m"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), MODEL_NUMERIC_FEATURES),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                MODEL_CATEGORICAL_FEATURES,
            ),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2)),
        ]
    )
    model.fit(X_train, y_train)
    predicted = model.predict(X_test)

    scores = {
        "train_count": len(X_train),
        "test_count": len(X_test),
        "mae": mean_absolute_error(y_test, predicted),
        "r2": r2_score(y_test, predicted),
    }
    display_cols = ["name_ko", "player", "squad", "nation"]
    comparison = model_df.loc[X_test.index, display_cols].join(X_test)
    comparison["actual_value_m"] = y_test.values
    comparison["predicted_value_m"] = predicted
    return model, scores, comparison


def build_prediction_input(age, position, league, minutes, goals, assists, starts):
    min_90s = minutes / 90 if minutes else np.nan
    return pd.DataFrame(
        [
            {
                "age": age,
                "primary_position": position,
                "league_ko": league,
                "minutes": minutes,
                "gls": goals,
                "ast": assists,
                "starts": starts,
                "goals_per90": goals / min_90s if min_90s else 0,
                "assists_per90": assists / min_90s if min_90s else 0,
            }
        ]
    )


def page_header():
    st.markdown(
        """
        <style>
        .stApp {
            background: #ffffff;
            color: #1f2933;
        }
        [data-testid="stSidebar"] {
            background: #f6f8fb;
            border-right: 1px solid #e5e9f0;
        }
        [data-testid="stSidebar"] * {
            color: #1f2933;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe2ea;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, .06);
        }
        .hero {
            padding: 22px 0 14px 0;
            border-bottom: 1px solid #e5e9f0;
            margin-bottom: 14px;
        }
        .hero h1 {
            color: #111827;
            font-size: 40px;
            line-height: 1.12;
            margin-bottom: 8px;
            letter-spacing: 0;
        }
        .hero p {
            color: #4b5563;
            font-size: 17px;
            max-width: 900px;
        }
        .league-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0 18px 0;
        }
        .league-mark {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 11px;
            border: 1px solid #d7dde6;
            border-radius: 8px;
            background: #fbfcfe;
            color: #1f2933;
            font-size: 14px;
            font-weight: 600;
        }
        .league-logo {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #111827;
            color: #111827;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0;
            background: #ffffff;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
        }
        .stDataFrame, .stTable {
            color: #1f2933;
        }
        </style>
        <div class="hero">
            <h1>축구 선수 시장가치 분석</h1>
            <p>5대리그 선수 기록을 살펴보고, 조건에 맞는 선수를 찾은 뒤 회귀 모델로 예상 시장가치를 확인하는 앱입니다.</p>
            <div class="league-strip">
                <div class="league-mark"><span class="league-logo">PL</span>프리미어리그</div>
                <div class="league-mark"><span class="league-logo">LL</span>라리가</div>
                <div class="league-mark"><span class="league-logo">SA</span>세리에 A</div>
                <div class="league-mark"><span class="league-logo">BL</span>분데스리가</div>
                <div class="league-mark"><span class="league-logo">L1</span>리그 1</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


uploaded_file = st.sidebar.file_uploader("CSV 파일 불러오기", type=["csv"])
prefer_online = st.sidebar.checkbox("온라인 데이터 불러오기 시도", value=False, help="인터넷 접속이 가능할 때만 켜세요. 접속이 차단되면 내장 데이터를 사용합니다.")
df, source_name = load_data(uploaded_file, prefer_online)
value_label = df["value_label"].iloc[0] if len(df) else "시장가치"

page_header()

st.sidebar.header("선수 찾기")
query = st.sidebar.text_input("이름으로 검색", placeholder="예: 손흥민, Son, 음바페")
position_options = ["전체", "공격수", "미드필더", "수비수", "골키퍼"]
selected_position = st.sidebar.selectbox("포지션", position_options)
league_options = ["전체"] + sorted(df["league_ko"].dropna().unique().tolist())
selected_league = st.sidebar.selectbox("리그", league_options)

age_min = int(max(15, math.floor(df["age"].min(skipna=True) or 15)))
age_max = int(max(50, math.ceil(df["age"].max(skipna=True) or 50)))
age_range = st.sidebar.slider("나이", age_min, age_max, (age_min, min(age_max, 35)))
max_value = float(np.nanmax(df["value_m"])) if len(df) else 300.0
value_slider_max = max(300.0, math.ceil(max_value / 10) * 10)
value_limit = st.sidebar.slider(f"최대 {value_label}", 1.0, value_slider_max, min(200.0, value_slider_max), step=1.0)
min_minutes = st.sidebar.slider("최소 출전 시간", 0, int(max(900, np.nanmax(df["minutes"]))), 300, step=100)

filtered = df.copy()
filtered = filtered[filtered["age"].between(age_range[0], age_range[1], inclusive="both")]
filtered = filtered[filtered["value_m"].le(value_limit)]
filtered = filtered[filtered["minutes"].fillna(0).ge(min_minutes)]
if selected_position != "전체":
    filtered = filtered[filtered["primary_position"].eq(selected_position)]
if selected_league != "전체":
    filtered = filtered[filtered["league_ko"].eq(selected_league)]
if query.strip():
    key = normalize_name(query)
    filtered = filtered[filtered["search_key"].str.contains(key, na=False)]

tab_recommend, tab_search, tab_league, tab_position, tab_model, tab_data = st.tabs(
    ["추천 선수", "선수 상세", "리그 비교", "포지션 분석", "시장가치 예측", "전체 데이터"]
)

with tab_recommend:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("조건에 맞는 선수", f"{len(filtered):,}명")
    with c2:
        metric_card("평균 나이", f"{filtered['age'].mean():.1f}세" if len(filtered) else "-")
    with c3:
        metric_card(f"평균 {value_label}", format_value(filtered["value_m"].mean()) if len(filtered) else "-")
    with c4:
        metric_card("평균 공격포인트", f"{filtered['g_plus_a'].mean():.1f}" if len(filtered) else "-")

    st.subheader("조건에 맞는 선수 목록")
    recommended = filtered.sort_values(["value_m", "g_plus_a", "minutes"], ascending=[False, False, False]).head(1000)
    display_table(recommended, value_label)

with tab_search:
    st.subheader("선수 상세 보기")
    search_base = filtered if query.strip() else df.head(50)
    if len(search_base) == 0:
        st.info("조건에 맞는 선수가 없습니다. 나이, 시장가치, 출전 시간 조건을 조금 넓혀보세요.")
    else:
        names = (search_base["name_ko"] + " · " + search_base["player"]).tolist()
        selected_name = st.selectbox("확인할 선수 선택", names)
        selected_player = search_base.iloc[names.index(selected_name)]
        career_text, strength_text, career_path = player_intro(selected_player)
        left, right = st.columns([1.1, 1])
        with left:
            st.markdown(f"### {selected_player['name_ko']}")
            st.write(f"영문 이름: {selected_player['player']}")
            st.write(f"소속팀: {selected_player['squad']}")
            st.write(f"리그: {selected_player['league_ko']}")
            st.write(f"국적: {selected_player['nation']}")
            st.write(f"포지션: {selected_player['position_ko']}")
            st.markdown("#### 기본 정보")
            st.info(career_text)
            st.markdown("#### 거쳐간 팀")
            st.write(career_path)
            st.markdown("#### 기록 해석")
            st.success(strength_text)
        with right:
            r1, r2 = st.columns(2)
            with r1:
                metric_card("나이", f"{selected_player['age']:.0f}세")
                metric_card("골", f"{selected_player['gls']:.0f}")
                metric_card("90분당 골", f"{selected_player['goals_per90']:.2f}")
            with r2:
                metric_card(value_label, format_value(selected_player["value_m"]))
                metric_card("도움", f"{selected_player['ast']:.0f}")
                metric_card("90분당 도움", f"{selected_player['assists_per90']:.2f}")

with tab_league:
    st.subheader("리그별 기록 비교")
    league_summary = (
        df.groupby("league_ko")
        .agg(
            선수수=("player", "count"),
            평균나이=("age", "mean"),
            평균가치=("value_m", "mean"),
            평균골=("gls", "mean"),
            평균도움=("ast", "mean"),
        )
        .sort_values("평균가치", ascending=False)
    )
    st.dataframe(
        league_summary.style.format({"평균나이": "{:.1f}", "평균가치": "€{:.1f}M", "평균골": "{:.1f}", "평균도움": "{:.1f}"}),
        width="stretch",
    )
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("#### 리그별 선수 수")
        st.bar_chart(league_summary["선수수"], width="stretch")
    with l2:
        st.markdown(f"#### 리그별 평균 {value_label}")
        st.bar_chart(league_summary["평균가치"], width="stretch")

with tab_position:
    st.subheader("포지션별 기록 비교")
    position_summary = (
        df.groupby("primary_position")
        .agg(
            선수수=("player", "count"),
            평균나이=("age", "mean"),
            평균가치=("value_m", "mean"),
            평균출전시간=("minutes", "mean"),
            평균공격포인트=("g_plus_a", "mean"),
        )
        .sort_values("선수수", ascending=False)
    )
    st.dataframe(
        position_summary.style.format({"평균나이": "{:.1f}", "평균가치": "€{:.1f}M", "평균출전시간": "{:.0f}", "평균공격포인트": "{:.1f}"}),
        width="stretch",
    )
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### 포지션별 선수 수")
        st.bar_chart(position_summary["선수수"], width="stretch")
    with p2:
        st.markdown("#### 포지션별 평균 공격포인트")
        st.bar_chart(position_summary["평균공격포인트"], width="stretch")

with tab_model:
    st.subheader("시장가치 예측 모델")
    st.write("나이, 포지션, 리그, 출전 시간, 골, 도움 기록을 사용해 선수의 예상 시장가치를 계산합니다.")

    model, scores, comparison = train_market_value_model(df)
    if model is None:
        st.warning("모델을 학습하려면 시장가치가 포함된 선수 기록이 최소 8명 이상 필요합니다.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("학습 데이터", f"{scores['train_count']}명")
        with c2:
            metric_card("검증 데이터", f"{scores['test_count']}명")
        with c3:
            metric_card("MAE", format_value(scores["mae"]), "평균 절대 오차입니다. 낮을수록 좋습니다.")
        with c4:
            metric_card("R²", f"{scores['r2']:.3f}", "모델 설명력입니다. 1에 가까울수록 좋습니다.")

        st.caption("사용 모델: 랜덤포레스트 회귀 / 데이터 분리: train_test_split / 성능 지표: MAE, R²")

        st.markdown("#### 검증 데이터 예측 결과")
        result_view = comparison.copy()
        result_view["실제 몸값"] = result_view["actual_value_m"].map(format_value)
        result_view["예측 몸값"] = result_view["predicted_value_m"].map(format_value)
        result_view = result_view.rename(
            columns={
                "name_ko": "선수",
                "player": "등록명",
                "squad": "소속팀",
                "nation": "국적",
                "age": "나이",
                "primary_position": "포지션",
                "league_ko": "리그",
                "minutes": "출전 시간",
                "gls": "골",
                "ast": "도움",
                "starts": "선발",
                "goals_per90": "90분당 골",
                "assists_per90": "90분당 도움",
            }
        )
        st.dataframe(
            result_view[["선수", "등록명", "소속팀", "국적", "나이", "포지션", "리그", "출전 시간", "골", "도움", "선발", "실제 몸값", "예측 몸값"]],
            width="stretch",
            hide_index=True,
            column_config={
                "선수": st.column_config.TextColumn("선수", width="medium"),
                "등록명": st.column_config.TextColumn("등록명", width="large"),
                "소속팀": st.column_config.TextColumn("소속팀", width="medium"),
            },
        )

        st.markdown("#### 선수 기록 직접 입력")
        p1, p2, p3 = st.columns(3)
        with p1:
            input_age = st.number_input("나이", min_value=15, max_value=45, value=24, step=1)
            input_position = st.selectbox("포지션", sorted(df["primary_position"].dropna().unique()))
        with p2:
            input_league = st.selectbox("리그", sorted(df["league_ko"].dropna().unique()))
            input_minutes = st.number_input("출전 시간", min_value=0, max_value=4500, value=2200, step=100)
        with p3:
            input_goals = st.number_input("골", min_value=0, max_value=80, value=10, step=1)
            input_assists = st.number_input("도움", min_value=0, max_value=50, value=5, step=1)
        input_starts = st.slider("선발 출전 수", min_value=0, max_value=40, value=25)

        input_data = build_prediction_input(
            input_age,
            input_position,
            input_league,
            input_minutes,
            input_goals,
            input_assists,
            input_starts,
        )
        predicted_value = model.predict(input_data)[0]
        st.metric("예상 시장가치", format_value(predicted_value))
        st.caption("입력한 기록을 학습된 회귀 모델에 넣어 계산한 예측값입니다.")

with tab_data:
    st.subheader("전체 선수 데이터")
    a, b, c = st.columns(3)
    with a:
        metric_card("데이터 출처", source_name)
    with b:
        metric_card("전체 선수", f"{len(df):,}명")
    with c:
        metric_card("포함 리그", f"{df['league_ko'].nunique()}개")
    display_table(df, value_label)
    st.download_button(
        "현재 데이터 CSV로 저장",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name="football_scout_players.csv",
        mime="text/csv",
    )
    st.caption("기본 데이터는 5대리그 주요 선수 기록을 정리한 CSV입니다. 더 정확한 시장가치를 쓰려면 market_value_m 컬럼이 포함된 CSV를 업로드하면 됩니다.")

