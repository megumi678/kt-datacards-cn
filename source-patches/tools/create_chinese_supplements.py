"""Create two explicitly identified supplements for incomplete official PDFs.

Exaction selection: exact cropped content from Chinese PDF appendix page 15.
Archsybarite: labelled unofficial translation of the original English TTS card;
weapon statistics are transcribed from that template, not inferred from another
operative. Original English card images remain the source of this supplement.
"""
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'layers/chinese-supplements'


def text(page, rect, value, size=8, color=(0,0,0)):
    if '\n' not in value and fitz.get_text_length(value, fontname='china-s', fontsize=size) <= rect[2]-rect[0]:
        page.insert_text((rect[0],rect[1]+size),value,fontname='china-s',fontsize=size,color=color)
        return
    spare = page.insert_textbox(fitz.Rect(rect), value, fontname='china-s', fontsize=size, color=color)
    if spare < 0:
        raise ValueError(f'Text does not fit: {value}')


def exaction():
    src = next((ROOT/'layers/warcom/staging_archive').glob('chi_*exaction_squad*.pdf'))
    with fitz.open(src) as original:
        assert '1 名强征小队' in original[14].get_text()
        for side, clip in [('front',(81,204,286,476)),('back',(81,483,286,655))]:
            doc = fitz.open()
            page = doc.new_page(width=194, height=338)
            page.draw_rect(page.rect, color=None, fill=(.03,.04,.05))
            text(page,(9,8,185,28),'强征小队 · 队伍选择',12,(1,1,1))
            page.draw_rect(fitz.Rect(8,32,186,34),color=None,fill=(1,.28,.02))
            area = fitz.Rect(8,39,186,291 if side=='front' else 210)
            page.show_pdf_page(area, original, 14, clip=fitz.Rect(clip), keep_proportion=True)
            text(page,(9,300,185,332), '来源：官方中文 PDF 第 15 页附录\n'+('翻面查看选人限制与原型。' if side=='front' else '选人限制与原型；名单见正面。'),6.5,(1,1,1))
            doc.save(DEST/f'exaction-selection-{side}.pdf')
            doc.close()


def archsybarite():
    weapons = [
        ('爆能手枪','4','3+','3/4','范围 8 英寸、穿刺 2'),
        ('毒晶手枪','4','3+','2/4','范围 8 英寸、致命 5+'),
        ('毒晶步枪','4','3+','2/4','致命 5+'),
        ('折磨之鞭','4','3+','3/5','残暴、致命 5+、震荡'),
        ('成套刀具','3','3+','3/4','—'),
        ('动力武器','4','3+','4/6','致命 5+'),
        ('毒刃','4','3+','4/5','致命 4+'),
    ]
    for side in ('front','back'):
        doc = fitz.open();page = doc.new_page(width=338, height=194)
        page.draw_rect(page.rect,color=None,fill=(.95,.93,.88))
        page.draw_rect(fitz.Rect(0,0,338,32),color=None,fill=(.04,.06,.07))
        text(page,(7,5,195,24),'阴谋团大享乐者',13,(1,1,1))
        text(page,(7,23,195,32),'执政官之手 · 队长 · 中文补译',6,(1,.58,.28))
        for x,label,value in [(200,'APL','2'),(234,'移动','7"'),(269,'豁免','4+'),(303,'耐伤','9')]:
            text(page,(x,3,x+34,14),label,7,(1,1,1))
            text(page,(x,15,x+34,31),value,10,(1,1,1))
        page.draw_rect(fitz.Rect(0,32,338,34),color=None,fill=(1,.28,.02))
        if side=='front':
            columns=[(8,112),(114,144),(146,176),(178,208),(210,332)]
            for (x,end),label in zip(columns,['名称','攻击','命中','伤害','武器规则']):
                text(page,(x,38,end,48),label,7)
            for i,row in enumerate(weapons):
                y=50+i*12.5
                if i%2:page.draw_rect(fitz.Rect(6,y-1,332,y+11.5),color=None,fill=(.87,.85,.81))
                for (x,end),value in zip(columns,row):text(page,(x,y,end,y+12),value,7)
            text(page,(8,143,330,179),'狡诈：在每个战略阶段的计划步骤中，如果该特工位于杀戮区，并且您在第一次机会选择跳过，则获得 1CP。判断本规则时，忽略任务包中的所有战略计划（若有）。',7)
        else:
            text(page,(9,45,329,143),'苦痛视界：在该特工每次激活期间限一次，若它在执行近战或射击行动时没有己方痛苦指示物，则当您选择一个有效射击目标或一名与之近战的敌方特工时，它可以获得一枚己方痛苦指示物。',9)
            text(page,(9,150,329,178),'补译来源：原项目的英文大享乐者卡。当前下载的官方中文 PDF 没有该数据卡，因此本卡不属于官方中文卡面；请在对战前核对规则版本。',7)
        page.draw_rect(fitz.Rect(0,182,338,194),color=None,fill=(.04,.06,.07))
        text(page,(8,185,330,194),'中文补译（非官方）｜数值沿用原英文模板｜'+('规则续于背面' if side=='front' else 'KABALITE ARCHSYBARITE'),6,(1,1,1))
        doc.save(DEST/f'archsybarite-{side}.pdf');doc.close()


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    exaction()
    archsybarite()
    print(f'Created four audited supplement faces in {DEST}')
