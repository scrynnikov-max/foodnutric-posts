from pathlib import Path
import fitz

path=Path("menu.pdf")
doc=fitz.open(path)
page=doc[0]
def replace(page, old, new, fontsize):
    rects=page.search_for(old)
    assert len(rects)==1,(old,len(rects))
    rect=rects[0]
    pix=page.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(rect.x0+1,rect.y0+1,rect.x0+2,rect.y0+2),alpha=False)
    bg=tuple(v/255 for v in pix.samples[:3])
    rect=fitz.Rect(rect.x0-1,rect.y0-1,rect.x1+2,rect.y1+2)
    page.add_redact_annot(rect,fill=bg)
    page.apply_redactions(images=0,graphics=0,text=0)
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    page.insert_text((rect.x0+1,rect.y0+fontsize),new,fontfile=font,fontname="dv",fontsize=fontsize,color=(.22,.22,.22))
replace(page,"20 мин","15–45 мин",13)
replace(page,"в среднем на блюдо","время приготовления",7.5)
page=doc[1]
rect=fitz.Rect(47,434,364,462)
pix=page.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(49,436,50,437),alpha=False)
bg=tuple(v/255 for v in pix.samples[:3])
page.add_redact_annot(rect,fill=bg)
page.apply_redactions(images=0,graphics=0,text=0)
font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
page.insert_font(fontname="dv",fontfile=font)
assert page.insert_textbox(rect,"Накануне — заготовка на 40 минут (стр. 4). Время приготовления отдельных блюд — от 15 до 45 минут.",fontname="dv",fontsize=9,lineheight=1.5,color=(.19,.23,.2))>=0
doc.save("menu-new.pdf",garbage=4,deflate=True)
check=fitz.open("menu-new.pdf")
assert len(check)==21
assert "15–45 мин" in check[0].get_text()
assert "от 15 до 45 минут" in check[1].get_text()
path.write_bytes(Path("menu-new.pdf").read_bytes())
print("Published verified 21-page menu PDF")
