#!/usr/bin/env python3
"""Build the public 15-dessert booklet from reviewed Markdown.
Keeps recipe photographs embedded in the previous edition where possible.
"""
import io, os, re, html, math
from pathlib import Path
import fitz
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, KeepTogether
from reportlab.lib.units import mm

ROOT=Path(__file__).resolve().parent.parent
SOURCE=(ROOT/'tools/desserts_source.md').read_text(encoding='utf-8')
OLD=ROOT/'tools/previous_desserts.pdf'
OUTPUT=ROOT/'desserts.pdf'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font))
pdfmetrics.registerFont(TTFont('DVB',bold))
BG=colors.HexColor('#F9F3EC')
INK=colors.HexColor('#28211E')
TERRA=colors.HexColor('#A54E35')
SAGE=colors.HexColor('#627B61')
W,H=A5
styles={
 'title':ParagraphStyle('title',fontName='DVB',fontSize=23,leading=29,textColor=INK,spaceAfter=14),
 'h':ParagraphStyle('h',fontName='DVB',fontSize=14,leading=18,textColor=INK,spaceAfter=8),
 'sub':ParagraphStyle('sub',fontName='DVB',fontSize=10,leading=14,textColor=TERRA,spaceAfter=6),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.2,leading=14,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='DV',fontSize=7.7,leading=11,textColor=INK,spaceAfter=5),
 'micro':ParagraphStyle('micro',fontName='DV',fontSize=7.1,leading=10,textColor=INK,spaceAfter=3),
 'tiny':ParagraphStyle('tiny',fontName='DV',fontSize=6.9,leading=9.3,textColor=INK,spaceAfter=3),
 'center':ParagraphStyle('center',fontName='DV',fontSize=9,leading=13,textColor=INK,alignment=TA_CENTER),
}
def P(t,style='body'):
    t=t
    return Paragraph(t,styles[style])
def inline(s):
    return re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',html.escape(s))
def paragraph(s,sty='body'):
    return Paragraph(inline(s),styles[sty])
def bg(c,doc):
    c.saveState()
    c.setFillColor(BG);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setStrokeColor(colors.HexColor('#E7DCD0'))
    c.line(12*mm,11*mm,W-12*mm,11*mm)
    c.setFont('DV',7);c.setFillColor(SAGE)
    c.drawString(12*mm,7.4*mm,'Татьяна  ·  15 десертов на каждый день')
    c.drawRightString(W-12*mm,7.4*mm,str(doc.page))
    c.restoreState()
blocks=re.split(r'(?=^### \d+\. )',SOURCE,flags=re.M)
recipes=[]
for block in blocks:
    m=re.match(r'### (\d+)\. ([^\n]+)\n',block)
    if not m:continue
    n=int(m.group(1));name=m.group(2)
    body=block.split('**Промпт для фото:**')[0]
    meta=re.search(r'\n([^\n]+(?:порци|штук|кусоч|печенье|батончик)[^\n]*)',body)
    nutrient=re.search(r'\*\*На [^:]+:\*\* ([^\n]+)',body)
    a=body.split('**Ингредиенты:**',1)[1].split('**Как готовить:**',1)[0]
    b=body.split('**Как готовить:**',1)[1]
    ingredients=re.findall(r'^- (.+)$',a,re.M)
    steps=re.findall(r'^\d+\. (.+)$',b,re.M)
    tip=re.search(r'\*\*Совет:\*\* ([^\n]+)',body)
    swap=re.search(r'\*\*Замена:\*\* ([^\n]+)',body)
    recipes.append(dict(n=n,name=name,meta=meta.group(1).strip() if meta else '',nutrient=nutrient.group(1) if nutrient else '',ing=ingredients,steps=steps,tip=tip.group(1) if tip else '',swap=swap.group(1) if swap else ''))
assert len(recipes)==15,len(recipes)
# Extract embedded food photos from the existing public booklet. No remote image generation.
photos={}
if OLD.exists():
    old=fitz.open(str(OLD))
    for i in range(15):
        page_idx=3+i
        if page_idx>=len(old):break
        page=old[page_idx]
        imgs=page.get_images(full=True)
        candidates=[]
        for im in imgs:
            try:
                data=old.extract_image(im[0])
                w,h=data['width'],data['height']
                if w>=350 and h>=250:
                    candidates.append((w*h,data['image']))
            except Exception:pass
        if candidates:
            photos[i+1]=max(candidates,key=lambda x:x[0])[1]
        else:
            # Original edition may flatten images into PDF drawing commands.
            # Rasterize only the top photograph area, not the old recipe text.
            crop=fitz.Rect(0,0,page.rect.width,page.rect.height*0.405)
            pix=page.get_pixmap(matrix=fitz.Matrix(1.8,1.8),clip=crop,alpha=False)
            photos[i+1]=pix.tobytes('png')
    print('previous pages',len(old),'recipe photos recovered',len(photos))
def image_for(n,maxw=123*mm,maxh=55*mm):
    data=photos.get(n)
    if not data:return None
    try:
        img=ImageReader(io.BytesIO(data))
        iw,ih=img.getSize()
        scale=min(maxw/iw,maxh/ih)
        return Image(io.BytesIO(data),width=iw*scale,height=ih*scale)
    except Exception as ex:
        print('photo skipped',n,str(ex));return None
story=[]
def add(*things):story.extend(things)
add(Spacer(1,20*mm),P('15 десертов<br/>на каждый день','title'),P('Рецепты из обычных продуктов — без запретов и обещаний чудес.','body'))
cover=image_for(1,110*mm,85*mm)
if cover:add(Spacer(1,8*mm),cover)
add(Spacer(1,8*mm),P('15 рецептов  ·  КБЖУ на порцию  ·  простые шаги','sub'),P('Бесплатная книга от проекта «Татьяна»','small'),PageBreak())
add(P('Сладкое — часть обычного питания','title'))
add(P('Не нужно отказываться от любимых десертов. Здесь собраны разные варианты: от быстрого мусса до чизкейка на выходные. Выбирай по вкусу, времени и продуктам, которые уже есть дома.'))
add(P('Как пользоваться сборником','h'))
for s in [
'КБЖУ — ориентир, а не точное число. Значения рассчитаны по усреднённым продуктам и зависят от марки, веса и размера порции.',
'Порция в рецепте нужна для расчёта. Она не устанавливает, сколько ты должна съесть.',
'Сладкое можно есть после еды или отдельно. Ориентируйся на голод, сытость и свой распорядок.',
'Заменяя ингредиенты, учитывай, что вкус, текстура и КБЖУ изменятся.',
'Если есть пищевая аллергия или заболевание, проверь ингредиенты и индивидуальные рекомендации врача.'
]:add(P('• '+s,'body'))
add(PageBreak(),P('Что приготовить сегодня?','title'))
for head,desc in [
('Быстро и без сложной готовки','№ 9 Шоколадный мусс; № 10 Банановое мороженое (заморозь бананы заранее); № 11 Морковный кекс в кружке.'),
('К чаю и с собой','№ 3 Мягкое яблочное печенье; № 5 Пирожное «картошка»; № 15 Овсяные батончики.'),
('Для гостей и выходных','№ 1 Йогуртовый чизкейк; № 8 Творожный тирамису; № 12 Панна-котта.')
]:add(P(head,'sub'),P(desc))
add(Spacer(1,6*mm),P('Все 15 рецептов','h'))
for r in recipes:add(P(f'{r["n"]:02d}. {r["name"]}','small'))
add(PageBreak())
for r in recipes:
    add(P(f'{r["n"]:02d}  {r["name"]}','h'))
    photo=image_for(r['n'])
    if photo:add(photo,Spacer(1,3*mm))
    add(P(r['meta'],'small'),P('На порцию: '+r['nutrient'],'sub'))
    left=[P('Ингредиенты','sub')]+[paragraph('• '+x,'tiny') for x in r['ing']]
    right=[P('Как готовить','sub')]+[paragraph(f'{i}. {x}','tiny') for i,x in enumerate(r['steps'],1)]
    t=Table([[left,right]],colWidths=[58*mm,64*mm],hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4*mm),('TOPPADDING',(0,0),(-1,-1),2*mm),('BOTTOMPADDING',(0,0),(-1,-1),2*mm)]))
    add(t)
    if r['tip']:add(Spacer(1,3*mm),paragraph('Совет: '+r['tip'],'small'))
    if r['swap']:add(paragraph('Замена: '+r['swap'],'small'))
    add(PageBreak())
add(P('Что дальше?','title'),P('Десерты помогают ответить на вопрос «что приготовить к чаю». Но остаются и другие вопросы: как организовать основные приёмы пищи, собрать удобное меню и сформировать привычки без строгих запретов.'))
add(P('Комплект «Питание без диет»','h'))
for x in ['Гайд «7 шагов к результату» — простые действия на каждый день.','Меню на 7 дней — идеи основных приёмов пищи.','Книга «Тарелка Татьяны» — 20 рецептов на каждый день.']:
    add(P('• '+x))
add(Spacer(1,4*mm),P('Стоимость комплекта: 870 ₽','sub'))
add(P('<link href="https://tatiananutri.ru/#guide" color="#A54E35"><u>Посмотреть комплект и способы оплаты на сайте</u></link>'))
add(Spacer(1,8*mm),P('Новые рецепты и разборы — в Telegram: @foodnutric','body'))
add(P('Материалы носят информационный характер и не заменяют индивидуальную медицинскую консультацию.','small'))
# The final PageBreak is omitted to avoid a blank page.
doc=SimpleDocTemplate(str(OUTPUT),pagesize=A5,rightMargin=12*mm,leftMargin=12*mm,topMargin=14*mm,bottomMargin=15*mm,title='15 десертов на каждый день',author='Проект Татьяна')
doc.build(story,onFirstPage=bg,onLaterPages=bg)
check=fitz.open(str(OUTPUT))
print('GENERATED',len(check),'pages',OUTPUT.stat().st_size,'bytes')
assert len(check)>=18,'Unexpectedly short booklet'
assert OUTPUT.stat().st_size>50000,'Booklet unexpectedly small'
