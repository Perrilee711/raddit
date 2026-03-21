#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "delivery" / "08-executive-delivery-summary.pptx"
EMU = 914400
SLIDE_W = 12192000
SLIDE_H = 6858000


SLIDES = [
    ("Demand Intelligence Platform", "老板汇报版交付摘要", ["一句话定义：把公开市场信号转化为客群、产品与增长决策的需求情报系统", "面向用户：CEO、业务线负责人、战略负责人", "当前状态：第一阶段完整闭环已交付", "当前形态：云上 API + Mac Worker + 在线工作台"], "2563EB"),
    ("为什么要做", "从零散研究升级到持续决策", ["过去依赖零散社媒观察、手工搜帖、静态快照式报告和个人经验判断", "直接导致：市场变化发现太慢、客群判断不稳定、产品包装脱离用户原话", "项目目标：把公开市场信号持续化、结构化、决策化"], "0EA5E9"),
    ("本次交付了什么", "不是单点爬虫，而是一套完整系统", ["Study 创建、关键词推荐与首跑", "Dashboard、Weekly Brief、Operations 三大核心界面", "thread/comment 实体底座 + 增量刷新", "browser / hot_threads / adaptive 调度", "stop、retry、worker 状态、运维告警"], "10B981"),
    ("产品与业务成果", "形成可被团队使用的研究工作流", ["选客群：高价值客群榜、热力图、机会分", "定产品：Packaging Studio、推荐产品包、价值主张", "看趋势：时间序列趋势图、异常波动、变化解释", "看执行：队列、任务、Worker 在线状态、停止当前爬取"], "F59E0B"),
    ("技术闭环", "云上 API + Mac Worker + 在线工作台", ["腾讯云 API 管理 Study、任务、调度与结果", "Mac Worker 认领 browser / hot_threads 任务并执行浏览器采集", "采集结果回写 raw / entities / payload，再由 Dashboard 读取", "具备多级队列、优先级编排、停止、重试与异常告警能力"], "8B5CF6"),
    ("测试与验收结果", "核心闭环已验证通过", ["系统可访问、Study 可创建、任务可入队、Mac Worker 可认领任务", "结果可回写、停止当前爬取、失败任务重试、Worker 在线状态可感知", "结论：第一阶段已达到“团队可用、可演示、可持续扩展”的门槛"], "EF4444"),
    ("当前上线资产", "代码、产品与运维入口已齐备", ["GitHub：github.com/Perrilee711/raddit", "团队工作台：http://43.162.90.26/", "API 健康检查：http://43.162.90.26/api/health", "Vercel 展示版：https://skill-deploy-jr9bh4v87v.vercel.app"], "2563EB"),
    ("下一阶段建议", "生产化增强 + 方法论复用", ["生产化增强：HTTPS API、正式域名、更正式鉴权、数据库化持久层", "方法论复用：沿用 BRD、PRD、UI、Technical、QA、Release 的完整交付结构", "管理层结论：项目已从单次研究脚本升级为可复用的需求情报系统样板"], "10B981"),
]


def emu_box(x: float, y: float, w: float, h: float):
    return tuple(int(v * EMU) for v in (x, y, w, h))


def paragraph(text: str, size_pt: int, bullet: bool = False) -> str:
    size = size_pt * 100
    bullet_xml = '<a:buChar char="•"/>' if bullet else "<a:buNone/>"
    mar_l = 420000 if bullet else 0
    return f"""
      <a:p>
        <a:pPr marL="{mar_l}" indent="-285750">{bullet_xml}</a:pPr>
        <a:r><a:rPr lang="zh-CN" sz="{size}"/><a:t>{escape(text)}</a:t></a:r>
        <a:endParaRPr lang="zh-CN" sz="{size}"/>
      </a:p>"""


def text_box(shape_id: int, name: str, box, paragraphs: str) -> str:
    x, y, w, h = box
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="{escape(name)}"/>
        <p:cNvSpPr txBox="1"/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:noFill/>
        <a:ln><a:noFill/></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" anchor="t"/>
        <a:lstStyle/>
        {paragraphs}
      </p:txBody>
    </p:sp>"""


def accent_bar(shape_id: int, color: str) -> str:
    x, y, w, h = emu_box(0.7, 0.7, 0.18, 1.0)
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="Accent"/>
        <p:cNvSpPr/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
        <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
        <a:ln><a:noFill/></a:ln>
      </p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
    </p:sp>"""


def slide_xml(title: str, subtitle: str, bullets: list[str], accent: str) -> str:
    title_p = paragraph(title, 24)
    subtitle_p = paragraph(subtitle, 14)
    body_p = "".join(paragraph(item, 18, bullet=True) for item in bullets)
    shapes = "".join(
        [
            accent_bar(2, accent),
            text_box(3, "Title", emu_box(0.95, 0.72, 10.8, 0.7), title_p),
            text_box(4, "Subtitle", emu_box(0.95, 1.45, 10.5, 0.45), subtitle_p),
            text_box(5, "Body", emu_box(1.05, 2.1, 11.1, 4.6), body_p),
        ]
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {shapes}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def write_pptx(output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    slide_count = len(SLIDES)
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>
  <Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>
  <Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>
""" + "\n".join(
        f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    ) + "\n</Types>"
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""
    app_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application><PresentationFormat>Widescreen</PresentationFormat><Slides>{slide_count}</Slides>
  <Notes>0</Notes><HiddenSlides>0</HiddenSlides><MMClips>0</MMClips><ScaleCrop>false</ScaleCrop>
  <HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Slides</vt:lpstr></vt:variant><vt:variant><vt:i4>{slide_count}</vt:i4></vt:variant></vt:vector></HeadingPairs>
  <TitlesOfParts><vt:vector size="{slide_count}" baseType="lpstr">{''.join('<vt:lpstr>Slide</vt:lpstr>' for _ in range(slide_count))}</vt:vector></TitlesOfParts>
  <Company>Fishgoo</Company><AppVersion>16.0000</AppVersion>
</Properties>"""
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Demand Intelligence Platform｜老板汇报版交付摘要</dc:title>
  <dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""
    theme_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Codex Theme">
  <a:themeElements>
    <a:clrScheme name="Codex"><a:dk1><a:srgbClr val="111827"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="10B981"/></a:accent2><a:accent3><a:srgbClr val="F59E0B"/></a:accent3><a:accent4><a:srgbClr val="8B5CF6"/></a:accent4><a:accent5><a:srgbClr val="0EA5E9"/></a:accent5><a:accent6><a:srgbClr val="EF4444"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Codex"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface="PingFang SC"/><a:cs typeface="Arial"/></a:majorFont><a:minorFont><a:latin typeface="Arial"/><a:ea typeface="PingFang SC"/><a:cs typeface="Arial"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Codex"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>"""
    slide_master = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld name="Codex Master"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""
    slide_master_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""
    slide_layout = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""
    slide_layout_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""
    slide_ids = "".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i}"/>'
        for i in range(1, slide_count + 1)
    )
    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" autoCompressPictures="0" saveSubsetFonts="1">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{slide_count + 1}"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/>
</p:presentation>"""
    presentation_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
""" + "\n".join(
        [f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>' for i in range(1, slide_count + 1)]
        + [
            f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
            f'<Relationship Id="rId{slide_count + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>',
            f'<Relationship Id="rId{slide_count + 3}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>',
            f'<Relationship Id="rId{slide_count + 4}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>',
        ]
    ) + "\n</Relationships>"
    slide_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""
    pres_props = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentationPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>"""
    view_props = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:viewPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:normalViewPr/></p:viewPr>"""
    table_styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>"""

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("docProps/app.xml", app_xml)
        zf.writestr("docProps/core.xml", core_xml)
        zf.writestr("ppt/presentation.xml", presentation)
        zf.writestr("ppt/_rels/presentation.xml.rels", presentation_rels)
        zf.writestr("ppt/slideMasters/slideMaster1.xml", slide_master)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels)
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels)
        zf.writestr("ppt/theme/theme1.xml", theme_xml)
        zf.writestr("ppt/presProps.xml", pres_props)
        zf.writestr("ppt/viewProps.xml", view_props)
        zf.writestr("ppt/tableStyles.xml", table_styles)
        for idx, (title, subtitle, bullets, accent) in enumerate(SLIDES, start=1):
            zf.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(title, subtitle, bullets, accent))
            zf.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    write_pptx(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
