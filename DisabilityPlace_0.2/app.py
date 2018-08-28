from flask import Flask, render_template, request, jsonify, redirect, url_for

from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from flask import session, escape

import json


app = Flask(__name__)
app.config.update({'SECRET_KEY':'password'})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB3.db'
db = SQLAlchemy(app)


# For more configuration options, check out the documentation
@app.route('/a')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


admin = Admin(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


class Place(db.Model):
    __tablename__ = 'Place'
    place_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    place_name = db.Column(db.String(20), nullable=False)
    place_address = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.FLOAT, nullable=False)
    lng = db.Column(db.FLOAT, nullable=False)
    category = db.Column(db.String(20), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'place_ID':self.place_ID,
            'place_name':self.place_name,
            'place_address' : self.place_address,
            'lat' : self.lat,
            'lng' : self.lng,
            'category' : self.category
        }


class Facility(db.Model):
    facility_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    facility_available_name = db.Column(db.String(50),nullable=False)
    facility_is_available = db.Column(db.String(20),nullable=False)
    place_ID = db.Column(db.Integer,db.ForeignKey("Place.place_ID"))

    @property
    def serialize(self):
        return {
            'facility_ID':self.facility_ID,
            'facility_available_name':self.facility_available_name,
            'facility_is_available':self.facility_is_available,
            'place_ID':self.place_ID
        }


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Place, db.session))
admin.add_view(ModelView(Facility, db.session))


@app.route('/', methods=['POST', 'GET'])
def place_Setting():
    content = request.args.get("content")
    print("ccc:",content)

    if request.method == 'GET':
        if content:
            places = Place.query.filter(Place.place_name.like('%' + content + '%'))
        else:
            places = Place.query.all()
    else :
        pass
        # lat = request.form['lat']
        # lng = request.form['lng']
        # print(lat, lng)
        # from CF import contentCF
        # cf = list(contentCF(lat, lng))
        # cf = map(int, cf)
        # places = Place.query.filter(Place.place_ID.in_(cf)).all()

    json_list = [i.serialize for i in places]
    faclist = ['객실 및 침실',
'경보 및 피난설비',
'샤워실 및 탈의실',
'세면대',
'욕실',
'음료대',
'자동 출입구(문)',
'자동 판매기',
'장애인 전용 주차구역',
'장애인용 관람석',
'장애인용 승강기',
'장애인용 화장실',
'점자블록',
'접수대 및 작업대',
'주출입구 높이차이 제거',
'주출입구 접근로',]
    return render_template('base2.html', places = json_list, faclist = faclist)


@app.route('/getData')
def getData():
    data = request.args.get('a')
    print("getdata place_id : ", data)
    places = Place.query.filter_by(place_ID=data)
    fac = Facility.query.filter_by(place_ID=data)

    p = [i.serialize for i in places]
    f = [i.serialize for i in fac]
    return jsonify(json.dumps(p), json.dumps(f))


@app.route('/listings-single/<place_id>')
def place_SingleListing(place_id):
    info = Place.query.filter_by(place_ID=place_id)
    facinfo = Facility.query.filter_by(place_ID=place_id)

    return render_template("listings-single-page.html", info=info.all(), facinfo=facinfo.all())

@app.route('/getCF', methods=['POST'])
def getCF():
    lat = request.form['lat']
    lng = request.form['lng']
    selectedfac = request.form['selectedfac']
    print(selectedfac, type(selectedfac))
    print(lat, lng)
    cf = list(contentCF(selectedfac, lat, lng))
    cf = list(map(int, cf))
    print(cf)
    places = Place.query.filter(Place.place_ID.in_(cf)).all()
    p = [i.serialize for i in places]
    print("places result serialize : ", p)
    return json.dumps(p)


import pandas as pd
from sklearn.neighbors import NearestNeighbors

def contentCF(selectedfac, lat, lng):
    places = Place.query
    facility = Facility.query

    dfplaces = pd.read_sql(places.statement, places.session.bind)
    dffac = pd.read_sql(facility.statement, facility.session.bind)

    dummy = pd.get_dummies(dffac, columns=['facility_available_name']).groupby(['place_ID'], as_index=False).sum()
    dummy = dummy.merge(dfplaces)

    print(dummy.info())
    dummy.drop('place_name', axis=1, inplace=True)
    dummy.drop('facility_ID', axis=1, inplace=True)
    dummy.drop(['category', 'place_address'], inplace=True, axis=1)

    dummy.columns = ['place_id','객실 및 침실',
'경보 및 피난설비',
'샤워실 및 탈의실',
'세면대',
'욕실',
'음료대',
'자동 출입구(문)',
'자동 판매기',
'장애인 전용 주차구역',
'장애인용 관람석',
'장애인용 승강기',
'장애인용 화장실',
'점자블록',
'접수대 및 작업대',
'주출입구 높이차이 제거',
'주출입구 접근로','lat', 'lng']

    X = dummy.iloc[:, 1:]
    print(X.head())
    nbrs = NearestNeighbors(n_neighbors=5).fit(X)

    t = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, lat, lng]

    s = selectedfac.split(',')
    print(s)
    for i in s:
        t[int(i)-1] += 1

    print("knn t ",t,"\n result :",nbrs.kneighbors([t]))

    return nbrs.kneighbors([t])[1][0]


# eda -->
@app.route('/test')
def test():

    return jsonify({'x':['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구',
       '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구',
       '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'],
                    'y' : [2777, 1855,  952, 2243, 1460,  950, 1111, 1376, 1754, 1228,  745,
       1026, 1006, 1051, 1697,  908, 1202, 3199,  910, 1343,  814, 1331,
       1197,  902, 1130],
                    } )


@app.route('/get_place')
def get_place():
    return jsonify({'x1':['강남구',
                          '강동구',
                          '강북구',
                          '강서구',
                          '관악구',
                          '광진구',
                          '구로구',
                          '금천구',
                          '노원구',
                          '도봉구',
                          '동대문구',
                          '동작구',
                          '마포구',
                          '서대문구',
                          '서초구',
                          '성동구',
                          '성북구',
                          '송파구',
                          '양천구',
                          '영등포구',
                          '용산구',
                          '은평구',
                          '종로구',
                          '중구',
                          '중랑구'],
                    'y1': [631,
                          461,
                          213,
                          582,
                          368,
                          209,
                          238,
                          309,
                          399,
                          309,
                          183,
                          247,
                          237,
                          244,
                          414,
                          222,
                          396,
                          624,
                          239,
                          323,
                          208,
                          476,
                          286,
                          235,
                          271],
                    'x2': ['종로구',
                         '중구',
                         '용산구',
                         '성동구',
                         '광진구',
                         '동대문구',
                         '중랑구',
                         '성북구',
                         '강북구',
                         '도봉구',
                         '노원구',
                         '은평구',
                         '서대문구',
                         '마포구',
                         '양천구',
                         '강서구',
                         '구로구',
                         '금천구',
                         '영등포구',
                         '동작구',
                         '관악구',
                         '서초구',
                         '강남구',
                         '송파구',
                         '강동구'],
                    'y2':[6064,
                         5694,
                         8116,
                         11770,
                         12514,
                         15893,
                         20034,
                         17529,
                         17377,
                         15196,
                         27436,
                         21301,
                         12644,
                         13250,
                         17232,
                         28717,
                         17289,
                         11059,
                         14351,
                         14590,
                         20103,
                         10774,
                         15617,
                         19790,
                         17413]
                   }
)


@app.route('/get_facility')
def get_facility():

    return jsonify({'x':['샤워실 및 탈의실', '욕실', '음료대', '자동 판매기', '접수대 및 작업대', '세면대	', '장애인용 관람석', '점자블록', '객실 및 침실',
                         '경보및 피난설비', '자동 출입구(문)	', '장애인용 화장실', '장애인용 승강기', '장애인 전용 주차구역', '주출입구 높이차이 제거', '주출입구 접근로'],
                    'y' : [144,
                            144,
                            340,
                            340,
                            342,
                            396,
                            561,
                            597,
                            693,
                            807,
                            3192,
                            3204,
                            3742,
                            5971,
                            6631,
                            7034],

                    "x1": ['객실 및 침실',
 '경보 및 피난설비',
 '샤워실 및 탈의실',
 '세면대',
 '욕실',
 '음료대',
 '자동 출입구(문)',
 '자동 판매기',
 '장애인 전용 주차구역',
 '장애인용 관람석',
 '장애인용 승강기',
 '장애인용 화장실',
 '점자블록',
 '접수대 및 작업대',
 '주출입구 높이차이 제거',
 '주출입구 접근로'], "y1" : [693,
 807,
 144,
 396,
 144,
 340,
 3192,
 340,
 5971,
 561,
 3742,
 3204,
 597,
 342,
 6631,
 7034]
                    } )


@app.route('/get_facility_category')
def get_facility_category():
    return jsonify({'toilet' : ['경찰서',
                                 '공중화장실',
                                 '교육원·직업훈련소·학원',
                                 '도서관',
                                 '미용원·목욕장',
                                 '보건소',
                                 '수련시설',
                                 '수퍼마켓·일용품 등의 도매·소매시장',
                                 '영화관/공연장',
                                 '우체국',
                                 '일반음식점',
                                 '종교집회장',
                                 '종합병원',
                                 '지역자치센터',
                                 '지하철',
                                 '학교'],
                    'ev' : ['경찰서',
                             '공중화장실',
                             '교육원·직업훈련소·학원',
                             '도서관',
                             '미용원·목욕장',
                             '보건소',
                             '복지시설',
                             '수련시설',
                             '수퍼마켓·일용품 등의 도매·소매시장',
                             '영화관/공연장',
                             '우체국',
                             '은행',
                             '일반숙박시설',
                             '일반음식점',
                             '전시장',
                             '종교집회장',
                             '종합병원',
                             '지역자치센터',
                             '지하철',
                             '학교'],
                    'in' : ['경찰서',
                             '공원',
                             '공중화장실',
                             '교육원·직업훈련소·학원',
                             '도서관',
                             '미용원·목욕장',
                             '보건소',
                             '복지시설',
                             '수련시설',
                             '수퍼마켓·일용품 등의 도매·소매시장',
                             '영화관/공연장',
                             '우체국',
                             '은행',
                             '일반숙박시설',
                             '일반음식점',
                             '전시장',
                             '종교집회장',
                             '종합병원',
                             '주차장',
                             '지역자치센터',
                             '체육관(운동장)',
                             '학교'],
                    'no_heigh': ['경찰서',
                                 '공원',
                                 '공중화장실',
                                 '교육원·직업훈련소·학원',
                                 '도서관',
                                 '미용원·목욕장',
                                 '보건소',
                                 '복지시설',
                                 '수련시설',
                                 '수퍼마켓·일용품 등의 도매·소매시장',
                                 '영화관/공연장',
                                 '우체국',
                                 '은행',
                                 '일반숙박시설',
                                 '일반음식점',
                                 '전시장',
                                 '종교집회장',
                                 '종합병원',
                                 '주차장',
                                 '지역자치센터',
                                 '체육관(운동장)',
                                 '학교'],
                    'view' : ['공중화장실', '도서관', '복지시설', '수련시설', '영화관/공연장', '일반숙박시설', '일반음식점'],
                    'parking': ['경찰서',
                                 '공원',
                                 '공중화장실',
                                 '교육원·직업훈련소·학원',
                                 '도서관',
                                 '미용원·목욕장',
                                 '보건소',
                                 '복지시설',
                                 '수련시설',
                                 '수퍼마켓·일용품 등의 도매·소매시장',
                                 '영화관/공연장',
                                 '우체국',
                                 '은행',
                                 '일반숙박시설',
                                 '일반음식점',
                                 '전시장',
                                 '종교집회장',
                                 '종합병원',
                                 '주차장',
                                 '지역자치센터',
                                 '체육관(운동장)',
                                 '학교'],
                    'auto_door' : ['경찰서',
                                 '공중화장실',
                                 '교육원·직업훈련소·학원',
                                 '도서관',
                                 '미용원·목욕장',
                                 '보건소',
                                 '복지시설',
                                 '수련시설',
                                 '수퍼마켓·일용품 등의 도매·소매시장',
                                 '영화관/공연장',
                                 '우체국',
                                 '은행',
                                 '일반숙박시설',
                                 '일반음식점',
                                 '전시장',
                                 '종교집회장',
                                 '종합병원',
                                 '지역자치센터',
                                 '체육관(운동장)',
                                 '학교'],
                    'wash' : ['공중화장실', '도서관', '복지시설', '수련시설', '영화관/공연장', '일반숙박시설', '종합병원'],
                    'dotblock' : ['경찰서',
                             '공중화장실',
                             '교육원·직업훈련소·학원',
                             '도서관',
                             '보건소',
                             '복지시설',
                             '수퍼마켓·일용품 등의 도매·소매시장',
                             '영화관/공연장',
                             '우체국',
                             '은행',
                             '일반숙박시설',
                             '전시장',
                             '종교집회장',
                             '종합병원',
                             '지역자치센터',
                             '학교'],
                    'bed' : ['공중화장실', '복지시설', '수련시설', '영화관/공연장', '일반숙박시설', '종합병원', '학교'],
                    'waring' : ['경찰서',
                                 '공원',
                                 '공중화장실',
                                 '도서관',
                                 '보건소',
                                 '복지시설',
                                 '영화관/공연장',
                                 '우체국',
                                 '일반숙박시설',
                                 '전시장',
                                 '종합병원',
                                 '지역자치센터',
                                 '학교'],
                    'dask' : ['경찰서', '공중화장실', '도서관', '보건소', '복지시설', '영화관/공연장', '우체국', '지역자치센터'],
                    'eatingwater' : ['경찰서', '공중화장실', '도서관', '보건소', '복지시설', '영화관/공연장', '우체국', '지역자치센터'],
                    'auto_dask' : ['경찰서', '공중화장실', '도서관', '보건소', '복지시설', '영화관/공연장', '우체국', '지역자치센터'],
                    'bath' : ['공중화장실', '복지시설'],
                    'rocker' : ['공중화장실', '복지시설'],
                    'toilety' : [99, 1099, 120, 40, 1, 2, 8, 62, 56, 89, 1, 4, 279, 278, 202, 864],
                    'evy' :  [40,
                             236,
                             666,
                             40,
                             1,
                             6,
                             458,
                             10,
                             150,
                             145,
                             12,
                             34,
                             70,
                             5,
                             37,
                             11,
                             649,
                             152,
                             204,
                             816],
                    'iny' : [250,
                             120,
                             451,
                             719,
                             51,
                             46,
                             6,
                             504,
                             11,
                             487,
                             184,
                             168,
                             43,
                             257,
                             494,
                             38,
                             454,
                             654,
                             97,
                             366,
                             27,
                             1607],
                    'no_heighy': [231,
                                 2,
                                 445,
                                 677,
                                 50,
                                 45,
                                 6,
                                 504,
                                 10,
                                 485,
                                 165,
                                 164,
                                 43,
                                 258,
                                 460,
                                 38,
                                 414,
                                 636,
                                 101,
                                 347,
                                 23,
                                 1527],
                    "viewy" : [43, 3, 138, 3, 124, 243, 7],
                    'parkingy' :  [234,
                                     2,
                                     312,
                                     681,
                                     48,
                                     1,
                                     5,
                                     463,
                                     12,
                                     158,
                                     156,
                                     156,
                                     38,
                                     56,
                                     464,
                                     29,
                                     420,
                                     612,
                                     44,
                                     353,
                                     24,
                                     1703],
                    'auto_doory' : [33,
                                     383,
                                     517,
                                     5,
                                     43,
                                     4,
                                     503,
                                     3,
                                     367,
                                     61,
                                     27,
                                     34,
                                     257,
                                     307,
                                     38,
                                     51,
                                     291,
                                     28,
                                     4,
                                     236],
                    'washy' : [57, 3, 139, 3, 60, 68, 66],
                    'dotblocky' : [1, 67, 43, 1, 1, 185, 13, 61, 2, 4, 22, 9, 1, 81, 2, 104],
                    'bedy' :     [86, 138, 3, 60, 247, 65, 94],
                    'waringy' : [32, 119, 126, 2, 4, 139, 61, 27, 68, 38, 66, 28, 97],
                    'dasky' : [32, 52, 4, 4, 138, 58, 27, 27],
                    'eatingwatery' : [32, 52, 2, 4, 138, 58, 27, 27],
                    'auto_dasky' :   [32, 52, 2, 4, 138, 58, 27, 27],
                    'bathy' : [5, 139],
                    'rockery' : [5, 139],
                    'toilets' : [1, 1, 2, 4, 8, 40, 56, 62, 89, 99, 120, 202, 278, 279, 864, 1099],
                    'evs' : [1,
 5,
 6,
 10,
 11,
 12,
 34,
 37,
 40,
 40,
 70,
 145,
 150,
 152,
 204,
 236,
 458,
 649,
 666,
 816],
                    'ins' : [6,
 11,
 27,
 38,
 43,
 46,
 51,
 97,
 120,
 168,
 184,
 250,
 257,
 366,
 451,
 454,
 487,
 494,
 504,
 654,
 719,
 1607],
                    'no_heighs' : [2,
 6,
 10,
 23,
 38,
 43,
 45,
 50,
 101,
 164,
 165,
 231,
 258,
 347,
 414,
 445,
 460,
 485,
 504,
 636,
 677,
 1527],
                    'views' : [3, 3, 7, 43, 124, 138, 243],
                    'parkings' : [1,
 2,
 5,
 12,
 24,
 29,
 38,
 44,
 48,
 56,
 156,
 156,
 158,
 234,
 312,
 353,
 420,
 463,
 464,
 612,
 681,
 1703],
                    'auto_doors' : [3,
 4,
 4,
 5,
 27,
 28,
 33,
 34,
 38,
 43,
 51,
 61,
 236,
 257,
 291,
 307,
 367,
 383,
 503,
 517],
                    'washs' : [3, 3, 57, 60, 66, 68, 139],
                    'dotblocks' : [1, 1, 1, 1, 2, 2, 4, 9, 13, 22, 43, 61, 67, 81, 104, 185],
                    'beds' : [3, 60, 65, 86, 94, 138, 247],
                    'warings' : [2, 4, 27, 28, 32, 38, 61, 66, 68, 97, 119, 126, 139],
                    'dasks' : [4, 4, 27, 27, 32, 52, 58, 138],
                    'eatingwaters' : [2, 4, 27, 27, 32, 52, 58, 138],
                    'auto_dasks' : [2, 4, 27, 27, 32, 52, 58, 138],
                    'baths' : [5, 139],
                    'rockers' : [5, 139],
                    'toiletr' : [1099, 864, 279, 278, 202, 120, 99, 89, 62, 56, 40, 8, 4, 2, 1, 1],
                    'toiletrn' : ['공중화장실', '학교', '종합병원', '지역자치센터', '지하철', '교육원·직업훈련소·학원', '경찰서', '우체국', '수퍼마켓·일용품 등의 도매·소매시장', '영화관/공연장', '도서관', '수련시설', '종교집회장', '보건소', '일반음식점', '미용원·목욕장'],
                    'evr' : [816,
                             666,
                             649,
                             458,
                             236,
                             204,
                             152,
                             150,
                             145,
                             70,
                             40,
                             40,
                             37,
                             34,
                             12,
                             11,
                             10,
                             6,
                             5,
                             1],
                    'evrn' : ['학교', '교육원·직업훈련소·학원', '종합병원', '복지시설', '공중화장실', '지하철', '지역자치센터', '수퍼마켓·일용품 등의 도매·소매시장', '영화관/공연장', '일반숙박시설', '도서관', '경찰서', '전시장', '은행', '우체국', '종교집회장', '수련시설', '보건소', '일반음식점', '미용원·목욕장'],
                    'inr' : [1607,
                             719,
                             654,
                             504,
                             494,
                             487,
                             454,
                             451,
                             366,
                             257,
                             250,
                             184,
                             168,
                             120,
                             97,
                             51,
                             46,
                             43,
                             38,
                             27,
                             11,
                             6],
                    'inrn' : ['학교', '교육원·직업훈련소·학원', '종합병원', '복지시설', '일반음식점', '수퍼마켓·일용품 등의 도매·소매시장', '종교집회장', '공중화장실', '지역자치센터', '일반숙박시설', '경찰서', '영화관/공연장', '우체국', '공원', '주차장', '도서관', '미용원·목욕장', '은행', '전시장', '체육관(운동장)', '수련시설', '보건소'],
                    'no_heighr' : [1527,
                                     677,
                                     636,
                                     504,
                                     485,
                                     460,
                                     445,
                                     414,
                                     347,
                                     258,
                                     231,
                                     165,
                                     164,
                                     101,
                                     50,
                                     45,
                                     43,
                                     38,
                                     23,
                                     10,
                                     6,
                                     2],
                    'no_heighrn' : ['학교', '교육원·직업훈련소·학원', '종합병원', '복지시설', '수퍼마켓·일용품 등의 도매·소매시장', '일반음식점', '공중화장실', '종교집회장', '지역자치센터', '일반숙박시설', '경찰서', '영화관/공연장', '우체국', '주차장', '도서관', '미용원·목욕장', '은행', '전시장', '체육관(운동장)', '수련시설', '보건소', '공원'],
                    'viewr' :  [243, 138, 124, 43, 7, 3, 3],
                    'viewrn' : ['일반숙박시설', '복지시설', '영화관/공연장', '공중화장실', '일반음식점', '수련시설', '도서관'],
                    'parkingr' : [1703,
                                 681,
                                 612,
                                 464,
                                 463,
                                 420,
                                 353,
                                 312,
                                 234,
                                 158,
                                 156,
                                 156,
                                 56,
                                 48,
                                 44,
                                 38,
                                 29,
                                 24,
                                 12,
                                 5,
                                 2,
                                 1],
                    "parkingrn" :   ['학교', '교육원·직업훈련소·학원', '종합병원', '일반음식점', '복지시설', '종교집회장', '지역자치센터', '공중화장실', '경찰서', '수퍼마켓·일용품 등의 도매·소매시장', '우체국', '영화관/공연장', '일반숙박시설', '도서관', '주차장', '은행', '전시장', '체육관(운동장)', '수련시설', '보건소', '공원', '미용원·목욕장'],
                    'auto_doorr' : [517,
                                 503,
                                 383,
                                 367,
                                 307,
                                 291,
                                 257,
                                 236,
                                 61,
                                 51,
                                 43,
                                 38,
                                 34,
                                 33,
                                 28,
                                 27,
                                 5,
                                 4,
                                 4,
                                 3],
                    'auto_doorrn' : ['교육원·직업훈련소·학원', '복지시설', '공중화장실', '수퍼마켓·일용품 등의 도매·소매시장', '일반음식점', '종합병원', '일반숙박시설', '학교', '영화관/공연장', '종교집회장', '미용원·목욕장', '전시장', '은행', '경찰서', '지역자치센터', '우체국', '도서관', '체육관(운동장)', '보건소', '수련시설'],
                    'washr' : [139, 68, 66, 60, 57, 3, 3],
                    'washrn' : ['복지시설', '일반숙박시설', '종합병원', '영화관/공연장', '공중화장실', '수련시설', '도서관'],
                    'dotblockr' : [185, 104, 81, 67, 61, 43, 22, 13, 9, 4, 2, 2, 1, 1, 1, 1],
                    'dotblockrn' : ['복지시설', '학교', '종합병원', '공중화장실', '영화관/공연장', '교육원·직업훈련소·학원', '일반숙박시설', '수퍼마켓·일용품 등의 도매·소매시장', '전시장','은행', '지역자치센터', '우체국', '종교집회장', '보건소', '도서관', '경찰서'],
                    'bedr' : [247, 138, 94, 86, 65, 60, 3],
                    'bedrn' : ['일반숙박시설', '복지시설', '학교', '공중화장실', '종합병원', '영화관/공연장', '수련시설'],
                    'waringr' : [139, 126, 119, 97, 68, 66, 61, 38, 32, 28, 27, 4, 2],
                    'waringrn' : ['복지시설', '공중화장실', '공원', '학교', '일반숙박시설', '종합병원', '영화관/공연장', '전시장', '경찰서', '지역자치센터', '우체국', '보건소', '도서관'],
                    'daskr' : [138, 58, 52, 32, 27, 27, 4, 4],
                    'daskrn' : ['복지시설', '영화관/공연장', '공중화장실', '경찰서', '지역자치센터', '우체국', '보건소', '도서관'],
                    'eatingwaterr' : [138, 58, 52, 32, 27, 27, 4, 2],
                    'eatingwaterrn' : ['복지시설', '영화관/공연장', '공중화장실', '경찰서', '지역자치센터', '우체국', '보건소', '도서관'],
                    'auto_daskr' : [138, 58, 52, 32, 27, 27, 4, 2],
                    'auto_daskrn' : ['복지시설', '영화관/공연장', '공중화장실', '경찰서', '지역자치센터', '우체국', '보건소', '도서관'],
                    'bathr' : [139, 5],
                    'bathrn' : ['복지시설', '공중화장실'],
                    'rockerr' : [139, 5],
                    'rockerrn' : ['복지시설', '공중화장실'],

                    'toilet_6' :  [ 160, 1611,  128,  202, 1099,    4],
                    'toilet_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'ev_6' : [ 448, 2167,  676,  204,  236,   11],
                    'ev_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'in_6' : [1704, 3598,  730,   97,  451,  454],
                    'in_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'no_heigh_6' : [1526, 3458,  687,  101,  445,  414],
                    'no_heigh_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'view_6' : [377, 138,   3,   0,  43,   0],
                    'view_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'parking_6' : [ 938, 3564,  693,   44,  312,  420],
                    'parking_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'auto_door_6' : [1082, 1156,  520,    0,  383,   51],
                    'auto_door_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'wash_6' : [131, 205,   3,   0,  57,   0],
                    'wash_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'dotblock_6' : [106, 380,  43,   0,  67,   1],
                    'dotblock_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'bed_6' : [307, 297,   3,   0,  86,   0],
                    'bed_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'waring_6' : [288, 393,   0,   0, 126,   0],
                    'waring_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    'dask_6' : [ 62, 228,   0,   0,  52,   0],
                    'dask_6_n' : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    "eatingwater_6" : [ 60, 228,   0,   0,  52,   0],
                    "eatingwater_6_n" : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    "auto_dask_6" : [ 60, 228,   0,   0,  52,   0],
                    "auto_dask_6_n" : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    "bath_6" : [  0, 139,   0,   0,   5,   0],
                    "bath_6_n" : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],
                    "rocker_6" : [  0, 139,   0,   0,   5,   0],
                    "rocker_6_n" : ['여가생활', '대표시설', '사설 교육시설', '교통', '화장실', '종교시설'],


                    'big_6': [648, 1355, 3471, 3486, 7249, 17929],
                    'big_6_n': ["교통", "종교시설", "화장실", "사설 교육시설", "여가생활", "대표시설"],

                    'people' : ['강남구',
 '강동구',
 '강북구',
 '강서구',
 '관악구',
 '광진구',
 '구로구',
 '금천구',
 '노원구',
 '도봉구',
 '동대문구',
 '동작구',
 '마포구',
 '서대문구',
 '서초구',
 '성동구',
 '성북구',
 '송파구',
 '양천구',
 '영등포구',
 '용산구',
 '은평구',
 '종로구',
 '중구',
 '중랑구'],
                    'people_r' : [15617,
 17413,
 17377,
 28717,
 20103,
 12514,
 17289,
 11059,
 27436,
 15196,
 15893,
 14590,
 13250,
 12644,
 10774,
 11770,
 17529,
 19790,
 17232,
 14351,
 8116,
 21301,
 6064,
 5694,
 20034],
                    'Gu_place' : ['강남구',
  '강동구',
  '강북구',
  '강서구',
  '관악구',
  '광진구',
  '구로구',
  '금천구',
  '노원구',
  '도봉구',
  '동대문구',
  '동작구',
  '마포구',
  '서대문구',
  '서초구',
  '성동구',
  '성북구',
  '송파구',
  '양천구',
  '영등포구',
  '용산구',
  '은평구',
  '종로구',
  '중구',
  '중랑구'],
                    'Gu_r' : [631,
  461,
  213,
  582,
  368,
  209,
  238,
  309,
  399,
  309,
  183,
  247,
  237,
  244,
  414,
  222,
  396,
  624,
  239,
  323,
  208,
  476,
  286,
  235,
  271],



                    })


@app.route('/eda')
def eda1():
    places = Place.query.all()
    json_list = [i.serialize for i in places]
    json_list = json_list[:4000]
    return render_template('dashboard-totalfacility.html', places=json_list)


@app.route('/eda2')
def eda2():
    return render_template('dashboard-facility-eda-map.html')


@app.route('/eda3')
def eda3():
    return render_template('dashboard-after-facility-map.html')


@app.route('/eda4')
def ed4():
    return render_template('dashoboard-total_big_6.html')


@app.route('/icon')
def icon():
    return render_template('pages-icons.html')


@app.route('/toilet')
def toilet():
    return render_template('toilet.html')


@app.route('/ev')
def ev():
    return render_template('ev.html')


@app.route('/in')
def ins():
    return render_template('in.html')


@app.route('/no_heigh')
def no_heigh():
    return render_template('no_heigh.html')


@app.route('/view')
def view():
    return render_template('view.html')


@app.route('/parking')
def parking():
    return render_template('parking.html')


@app.route('/auto_door')
def auto_door():
    return render_template('auto_door.html')


@app.route('/wash')
def wash():
    return render_template('wash.html')


@app.route('/dotblock')
def dotblock():
    return render_template('dotblock.html')


@app.route('/bed')
def bed():
    return render_template('bed.html')


@app.route('/waring')
def waring():
    return render_template('waring.html')


@app.route('/dask')
def dask():
    return render_template('dask.html')


@app.route('/eatingwater')
def eatingwater():
    return render_template('eatingwater.html')


@app.route('/auto_dask')
def auto_dask():
    return render_template('auto_dask.html')


@app.route('/bath')
def bath():
    return render_template('bath.html')


@app.route('/rocker')
def rocker():
    return render_template('rocker.html')

@app.route('/eda5')
def eda5():
    return render_template('dashboard-totalfacility2.html')
@app.route('/eda6')
def eda6():
    return render_template('dashboard-totalfacility3.html')

@app.route('/eda7')
def eda7():
    return render_template('dashboard-totalfacility4.html')



@app.route('/base3')
def base3():
    places = Place.query.all()
    json_list = [i.serialize for i in places]
    faclist = ['객실 및 침실',
               '경보 및 피난설비',
               '샤워실 및 탈의실',
               '세면대',
               '욕실',
               '음료대',
               '자동 출입구(문)',
               '자동 판매기',
               '장애인 전용 주차구역',
               '장애인용 관람석',
               '장애인용 승강기',
               '장애인용 화장실',
               '점자블록',
               '접수대 및 작업대',
               '주출입구 높이차이 제거',
               '주출입구 접근로', ]
    return render_template('base3.html', places=json_list, faclist=faclist)


# eda-->

if __name__ == '__main__':
    app.run()











