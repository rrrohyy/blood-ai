"""
blood.ai 샘플 건강검진 PDF 생성기
가상 인물: 이서현(F), 1988-06-15
"""
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# 한국어 폰트 등록
pdfmetrics.registerFont(TTFont('KR', '/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
pdfmetrics.registerFont(TTFont('KR-B', '/System/Library/Fonts/Supplemental/AppleGothic.ttf'))

W, H = A4  # 595, 842

def draw_hanaro(filename, date, data):
    """하나로 의료재단 포맷 PDF"""
    c = canvas.Canvas(filename, pagesize=A4)

    def kr(x, y, text, size=10, bold=False):
        c.setFont('KR', size)
        c.drawString(x, y, text)

    def en(x, y, text, size=10):
        c.setFont('Helvetica', size)
        c.drawString(x, y, text)

    def line_sep(y):
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(1.5*cm, y, W-1.5*cm, y)

    y = H - 1.5*cm

    # 헤더
    c.setFillColorRGB(0.0, 0.35, 0.27)
    c.rect(0, H-2.8*cm, W, 2.8*cm, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    kr(2*cm, H-1.5*cm, '하나로 의료재단', 18)
    en(2*cm, H-2.2*cm, 'Health Check-up Report', 10)
    c.setFillColorRGB(0, 0, 0)

    y = H - 3.5*cm

    # 수검자 정보
    kr(2*cm, y, f'검진일: {date}', 11); y -= 0.6*cm
    kr(2*cm, y, '성명: 이서현   성별: 여   생년월일: 1988-06-15', 10); y -= 0.6*cm
    kr(2*cm, y, '검진기관: 하나로 의료재단 강남센터', 10); y -= 0.8*cm

    line_sep(y); y -= 0.5*cm

    # 섹션 제목
    c.setFillColorRGB(0.0, 0.35, 0.27)
    kr(2*cm, y, '[ 혈액 검사 결과 ]', 12)
    c.setFillColorRGB(0, 0, 0)
    y -= 0.8*cm

    # 이상지질혈증
    kr(2*cm, y, '■ 이상지질혈증 검사', 11); y -= 0.6*cm

    items = []
    if 'TC' in data:
        items.append(('총콜레스테롤', str(data['TC']) + (' H' if data['TC'] > 200 else ''), 'mg/dL', '<200'))
    if 'LDL' in data:
        flag = ' H' if data['LDL'] > 130 else ''
        items.append(('LDL 콜레스테롤 (Calculated)', str(data['LDL']) + flag, 'mg/dL', '<130'))
    if 'HDL' in data:
        items.append(('HDL 콜레스테롤', str(data['HDL']), 'mg/dL', '>60'))
    if 'TG' in data:
        items.append(('중성지방', str(data['TG']) + (' H' if data['TG'] > 150 else ''), 'mg/dL', '<150'))

    for name, val, unit, ref in items:
        kr(2.5*cm, y, name, 10)
        en(11*cm, y, val, 10)
        en(13.5*cm, y, unit, 9)
        kr(15.5*cm, y, f'(기준 {ref})', 9)
        y -= 0.55*cm

    y -= 0.3*cm
    kr(2*cm, y, '■ 혈당 검사', 11); y -= 0.6*cm
    if 'GLUCOSE' in data:
        kr(2.5*cm, y, 'Glucose 공복혈당', 10)
        en(11*cm, y, str(data['GLUCOSE']) + (' H' if data['GLUCOSE'] > 100 else ''), 10)
        en(13.5*cm, y, 'mg/dL', 9)
        y -= 0.55*cm

    y -= 0.3*cm
    kr(2*cm, y, '■ 빈혈 검사', 11); y -= 0.6*cm
    if 'HB' in data:
        kr(2.5*cm, y, 'Hemoglobin 헤모글로빈', 10)
        en(11*cm, y, str(data['HB']), 10)
        en(13.5*cm, y, 'g/dL', 9)
        y -= 0.55*cm
    if 'FERRITIN' in data:
        kr(2.5*cm, y, 'Ferritin 혈청 페리틴', 10)
        en(11*cm, y, str(data['FERRITIN']), 10)
        en(13.5*cm, y, 'ng/mL', 9)
        y -= 0.55*cm

    y -= 0.3*cm
    kr(2*cm, y, '■ 간·신장 기능', 11); y -= 0.6*cm
    if 'ALT' in data:
        kr(2.5*cm, y, 'SGPT(ALT) 간수치', 10)
        en(11*cm, y, str(data['ALT']), 10)
        en(13.5*cm, y, 'IU/L', 9)
        y -= 0.55*cm
    if 'CR' in data:
        kr(2.5*cm, y, 'Creatinine 크레아티닌', 10)
        en(11*cm, y, str(data['CR']), 10)
        en(13.5*cm, y, 'mg/dL', 9)
        y -= 0.55*cm
    if 'EGFR' in data:
        kr(2.5*cm, y, 'e-GFR 사구체여과율', 10)
        en(11*cm, y, str(data['EGFR']), 10)
        en(13.5*cm, y, 'mL/min', 9)
        y -= 0.55*cm

    y -= 0.3*cm
    kr(2*cm, y, '■ 기타', 11); y -= 0.6*cm
    if 'URIC' in data:
        kr(2.5*cm, y, 'Uric acid 요산', 10)
        en(11*cm, y, str(data['URIC']) + (' H' if data['URIC'] > 5.7 else ''), 10)
        en(13.5*cm, y, 'mg/dL', 9)
        y -= 0.55*cm
    if 'WBC' in data:
        kr(2.5*cm, y, 'WBC 백혈구', 10)
        en(11*cm, y, str(data['WBC']), 10)
        en(13.5*cm, y, '10³/μL', 9)
        y -= 0.55*cm

    if 'TSH' in data or 'VITD' in data:
        y -= 0.3*cm
        kr(2*cm, y, '■ 호르몬 / 비타민', 11); y -= 0.6*cm
        if 'TSH' in data:
            kr(2.5*cm, y, 'TSH: ' + str(data['TSH']), 10)
            en(11*cm, y, str(data['TSH']) + (' H' if data['TSH'] > 4.2 else ''), 10)
            en(13.5*cm, y, 'μIU/mL', 9)
            y -= 0.55*cm
        if 'VITD' in data:
            kr(2.5*cm, y, '25-(OH)Vit.D total: ' + str(data['VITD']), 10)
            en(11*cm, y, str(data['VITD']) + (' L' if data['VITD'] < 20 else ''), 10)
            en(13.5*cm, y, 'ng/mL', 9)
            y -= 0.55*cm

    # 푸터
    line_sep(1.8*cm)
    c.setFont('Helvetica', 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(2*cm, 1.2*cm, 'This is a SAMPLE document generated for blood.ai demo purposes only.')

    c.save()
    print(f'  생성: {filename}')


def draw_gc(filename, date, data):
    """GC 녹십자아이메드 포맷 PDF"""
    c = canvas.Canvas(filename, pagesize=A4)

    def kr(x, y, text, size=10):
        c.setFont('KR', size)
        c.drawString(x, y, text)

    def en(x, y, text, size=10):
        c.setFont('Helvetica', size)
        c.drawString(x, y, text)

    y = H - 1.5*cm

    # 헤더
    c.setFillColorRGB(0.08, 0.39, 0.75)
    c.rect(0, H-2.8*cm, W, 2.8*cm, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    kr(2*cm, H-1.5*cm, 'GC녹십자아이메드', 18)
    en(2*cm, H-2.2*cm, 'GC녹십자 아이메드 건강증진센터', 10)
    c.setFillColorRGB(0, 0, 0)

    y = H - 3.5*cm
    kr(2*cm, y, f'의뢰일자: {date}', 11); y -= 0.6*cm
    kr(2*cm, y, '성명: 이서현   성별: 여   생년월일: 1988-06-15', 10); y -= 0.8*cm

    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 0.5*cm

    c.setFillColorRGB(0.08, 0.39, 0.75)
    kr(2*cm, y, '[ 혈액 검사 결과 ]', 12)
    c.setFillColorRGB(0, 0, 0)
    y -= 0.8*cm

    items_ko = []
    if 'TC' in data:
        items_ko.append(('Total cholesterol 총콜레스테롤', data['TC'], 'mg/dL', '<200'))
    if 'LDL' in data:
        items_ko.append(('LDL 콜레스테롤', data['LDL'], 'mg/dL', '<130'))
    if 'HDL' in data:
        items_ko.append(('HDL 콜레스테롤', data['HDL'], 'mg/dL', '>60'))
    if 'TG' in data:
        items_ko.append(('Triglyceride 중성지방', data['TG'], 'mg/dL', '<150'))
    if 'GLUCOSE' in data:
        items_ko.append(('혈당(식전) 공복혈당', data['GLUCOSE'], 'mg/dL', '<100'))
    if 'HB' in data:
        items_ko.append(('Hb(혈색소)', data['HB'], 'g/dL', '≥12'))
    if 'FERRITIN' in data:
        items_ko.append(('Ferritin', data['FERRITIN'], 'ng/mL', '>12'))
    if 'ALT' in data:
        items_ko.append(('ALT(혈청GPT)', data['ALT'], 'IU/L', '<40'))
    if 'CR' in data:
        items_ko.append(('Cr(크레아티닌)', data['CR'], 'mg/dL', '<1.0'))
    if 'EGFR' in data:
        items_ko.append(('GFR 사구체여과율', data['EGFR'], 'mL/min', '>60'))
    if 'URIC' in data:
        items_ko.append(('Uric acid 요산', data['URIC'], 'mg/dL', '<5.7'))
    if 'WBC' in data:
        items_ko.append(('WBC 백혈구', data['WBC'], '10³/μL', '4~10'))
    if 'TSH' in data:
        items_ko.append(('TSH 갑상선자극호르몬', data['TSH'], 'μIU/mL', '0.4~4.2'))
    if 'VITD' in data:
        items_ko.append(('비타민(Vitamin)D3', data['VITD'], 'ng/mL', '>20'))

    for name, val, unit, ref in items_ko:
        kr(2.5*cm, y, name, 10)
        flag = ''
        if isinstance(val, float):
            flag = f'{val}'
        else:
            flag = str(val)
        en(11*cm, y, flag, 10)
        en(13.5*cm, y, unit, 9)
        kr(15.5*cm, y, f'(기준 {ref})', 9)
        y -= 0.55*cm

    c.setFont('Helvetica', 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.line(1.5*cm, 1.8*cm, W-1.5*cm, 1.8*cm)
    c.drawString(2*cm, 1.2*cm, 'This is a SAMPLE document generated for blood.ai demo purposes only.')

    c.save()
    print(f'  생성: {filename}')


# ── 샘플 데이터 (이서현, F, 1988-06-15) ──────────────────

samples = [
    {
        'type': 'hanaro',
        'file': 'sample_하나로_2021-09.pdf',
        'date': '2021-09-15',
        'data': {
            'TC': 220, 'LDL': 131, 'HDL': 71, 'TG': 98,
            'HB': 13.5, 'FERRITIN': 42,
            'ALT': 22, 'CR': 0.72, 'EGFR': 88,
            'URIC': 6.5, 'WBC': 4.5,
        }
    },
    {
        'type': 'gc',
        'file': 'sample_GC녹십자_2023-03.pdf',
        'date': '2023-03-22',
        'data': {
            'TC': 238, 'LDL': 142, 'HDL': 68, 'TG': 119,
            'GLUCOSE': 96, 'VITD': 12.3, 'TSH': 2.81,
            'HB': 12.1, 'FERRITIN': 28,
            'ALT': 19, 'CR': 0.74, 'EGFR': 85,
            'URIC': 6.8, 'WBC': 4.2,
        }
    },
    {
        'type': 'hanaro',
        'file': 'sample_하나로_2024-06.pdf',
        'date': '2024-06-10',
        'data': {
            'TC': 245, 'LDL': 148, 'HDL': 70, 'TG': 128,
            'GLUCOSE': 98,
            'HB': 12.8, 'FERRITIN': 19,
            'ALT': 21, 'CR': 0.77, 'EGFR': 82,
            'URIC': 6.9, 'WBC': 4.8,
        }
    },
    {
        'type': 'hanaro',
        'file': 'sample_하나로_2025-11.pdf',
        'date': '2025-11-18',
        'data': {
            'TC': 263, 'LDL': 161, 'HDL': 68, 'TG': 142,
            'GLUCOSE': 101, 'VITD': 7.8, 'TSH': 5.12,
            'HB': 12.8, 'FERRITIN': 14,
            'ALT': 16, 'CR': 0.79, 'EGFR': 80,
            'URIC': 7.2, 'WBC': 5.1,
        }
    },
]

import os
out_dir = os.path.dirname(os.path.abspath(__file__))
print(f'샘플 PDF 생성 중... → {out_dir}')

for s in samples:
    path = os.path.join(out_dir, s['file'])
    if s['type'] == 'hanaro':
        draw_hanaro(path, s['date'], s['data'])
    else:
        draw_gc(path, s['date'], s['data'])

print('\n완료! 4개 파일 생성됨.')
print('혈액.ai PDF 파싱 탭에서 업로드해서 테스트하세요.')


# ── 추가 샘플: 박재원 (M, 1980-03-20) — 몸 안 좋은 케이스 2년치 ──

def draw_hanaro_m(filename, date, data):
    """하나로 포맷 — 박재원(남)"""
    c = canvas.Canvas(filename, pagesize=A4)

    def kr(x, y, text, size=10):
        c.setFont('KR', size)
        c.drawString(x, y, text)
    def en(x, y, text, size=10):
        c.setFont('Helvetica', size)
        c.drawString(x, y, text)
    def line_sep(y):
        c.setStrokeColorRGB(0.8,0.8,0.8)
        c.line(1.5*cm, y, W-1.5*cm, y)

    # 헤더
    c.setFillColorRGB(0.0,0.35,0.27)
    c.rect(0, H-2.8*cm, W, 2.8*cm, fill=True, stroke=False)
    c.setFillColorRGB(1,1,1)
    kr(2*cm, H-1.5*cm, '하나로 의료재단', 18)
    en(2*cm, H-2.2*cm, 'Health Check-up Report', 10)
    c.setFillColorRGB(0,0,0)

    y = H-3.5*cm
    kr(2*cm, y, f'검진일: {date}', 11); y-=0.6*cm
    kr(2*cm, y, '성명: 박재원   성별: 남   생년월일: 1980-03-20', 10); y-=0.6*cm
    kr(2*cm, y, '검진기관: 하나로 의료재단 강남센터', 10); y-=0.8*cm
    line_sep(y); y-=0.5*cm

    c.setFillColorRGB(0.0,0.35,0.27)
    kr(2*cm, y, '[ 혈액 검사 결과 ]', 12)
    c.setFillColorRGB(0,0,0); y-=0.8*cm

    def row(label, val, unit, ref, high=False, low=False):
        nonlocal y
        kr(2.5*cm, y, label, 10)
        flag = str(val) + (' H' if high else ' L' if low else '')
        en(11*cm, y, flag, 10)
        en(13.5*cm, y, unit, 9)
        kr(15.5*cm, y, f'(기준 {ref})', 9)
        y-=0.55*cm

    kr(2*cm, y, '■ 이상지질혈증 검사', 11); y-=0.6*cm
    row('총콜레스테롤', data['TC'], 'mg/dL', '<200', high=data['TC']>200)
    row('LDL 콜레스테롤 (Calculated)', data['LDL'], 'mg/dL', '<130', high=data['LDL']>130)
    row('HDL 콜레스테롤', data['HDL'], 'mg/dL', '>40', low=data['HDL']<40)
    row('중성지방', data['TG'], 'mg/dL', '<150', high=data['TG']>150)

    y-=0.3*cm; kr(2*cm, y, '■ 혈당 검사', 11); y-=0.6*cm
    row('Glucose 공복혈당', data['GLUCOSE'], 'mg/dL', '<100', high=data['GLUCOSE']>100)

    y-=0.3*cm; kr(2*cm, y, '■ 간·신장 기능', 11); y-=0.6*cm
    row('SGPT(ALT) 간수치', data['ALT'], 'IU/L', '<40', high=data['ALT']>40)
    row('AST(GOT)', data['AST'], 'IU/L', '<40', high=data['AST']>40)
    row('Creatinine 크레아티닌', data['CR'], 'mg/dL', '<1.2', high=data['CR']>1.2)
    row('e-GFR 사구체여과율', data['EGFR'], 'mL/min', '>60', low=data['EGFR']<60)

    y-=0.3*cm; kr(2*cm, y, '■ 빈혈 검사', 11); y-=0.6*cm
    row('Hemoglobin 헤모글로빈', data['HB'], 'g/dL', '>13')
    row('Ferritin 혈청 페리틴', data['FERRITIN'], 'ng/mL', '>30', low=data['FERRITIN']<30)

    y-=0.3*cm; kr(2*cm, y, '■ 기타', 11); y-=0.6*cm
    row('Uric acid 요산', data['URIC'], 'mg/dL', '<7.0(남)', high=data['URIC']>7.0)
    row('WBC 백혈구', data['WBC'], '10³/μL', '4~10')

    y-=0.3*cm; kr(2*cm, y, '■ 호르몬 / 비타민', 11); y-=0.6*cm
    row('TSH 갑상선자극호르몬', data['TSH'], 'μIU/mL', '0.4~4.2', high=data['TSH']>4.2)
    row('25-(OH)Vit.D total', data['VITD'], 'ng/mL', '>20', low=data['VITD']<20)

    line_sep(1.8*cm)
    c.setFont('Helvetica',8); c.setFillColorRGB(0.5,0.5,0.5)
    c.drawString(2*cm, 1.2*cm, 'This is a SAMPLE document generated for blood.ai demo purposes only.')
    c.save()
    print(f'  생성: {filename}')


bad_samples = [
    {
        'file': 'sample_박재원_2024-01.pdf',
        'date': '2024-01-08',
        'data': {
            'TC':252,'LDL':168,'HDL':38,'TG':198,
            'GLUCOSE':118,
            'ALT':52,'AST':44,'CR':0.98,'EGFR':82,
            'HB':15.2,'FERRITIN':28,
            'URIC':7.8,'WBC':7.2,
            'TSH':1.8,'VITD':9.5,
        }
    },
    {
        'file': 'sample_박재원_2024-07.pdf',
        'date': '2024-07-15',
        'data': {
            'TC':265,'LDL':175,'HDL':36,'TG':218,
            'GLUCOSE':124,
            'ALT':61,'AST':55,'CR':1.02,'EGFR':78,
            'HB':15.0,'FERRITIN':24,
            'URIC':8.1,'WBC':7.8,
            'TSH':2.1,'VITD':7.2,
        }
    },
    {
        'file': 'sample_박재원_2024-12.pdf',
        'date': '2024-12-03',
        'data': {
            'TC':278,'LDL':182,'HDL':34,'TG':243,
            'GLUCOSE':128,
            'ALT':78,'AST':68,'CR':1.08,'EGFR':74,
            'HB':14.5,'FERRITIN':20,
            'URIC':8.8,'WBC':8.5,
            'TSH':3.2,'VITD':6.1,
        }
    },
    {
        'file': 'sample_박재원_2025-06.pdf',
        'date': '2025-06-20',
        'data': {
            'TC':291,'LDL':188,'HDL':33,'TG':267,
            'GLUCOSE':132,
            'ALT':92,'AST':81,'CR':1.12,'EGFR':70,
            'HB':14.2,'FERRITIN':17,
            'URIC':9.2,'WBC':9.1,
            'TSH':4.8,'VITD':5.8,
        }
    },
]

print('\n박재원(남) 건강 악화 케이스 생성 중...')
for s in bad_samples:
    draw_hanaro_m(os.path.join(out_dir, s['file']), s['date'], s['data'])

print('\n완료! 박재원 4개 파일 추가 생성됨.')
