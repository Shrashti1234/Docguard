"""Render fictional Hindi examples with MuPDF's shaped Unicode text renderer."""
from pathlib import Path
import pymupdf

root = Path(__file__).resolve().parents[1]/'assets/examples'
root.mkdir(parents=True, exist_ok=True)
for variant, amount in [('original', '1,250'), ('edited', '1,950')]:
    html = f'''<html><body>
    <p class="kicker">काल्पनिक दस्तावेज़ · केवल शोध के लिए</p>
    <h1>सहयोग स्टोर</h1><p>खरीद की रसीद</p>
    <div class="rule"></div>
    <p>रसीद संख्या: DEMO-1024<br>दिनांक: 26/10/2026</p>
    <table><tr><th>विवरण</th><th>राशि (रु.)</th></tr>
    <tr><td>किताबें</td><td>750</td></tr><tr><td>स्टेशनरी</td><td>300</td></tr>
    <tr><td>फाइलें</td><td>200</td></tr><tr class="total"><td>कुल राशि</td><td>{amount}</td></tr></table>
    <p class="foot">यह एक कृत्रिम उदाहरण है। किसी वास्तविक व्यक्ति या दुकान से संबंधित नहीं है।</p>
    </body></html>'''
    css = '''body{font-family:sans-serif;font-size:15px;color:#24352e;padding:22px}
    h1{font-size:30px;margin:10px 0}.kicker{font-size:10px;color:#67776e}
    .rule{border-bottom:2px solid #315f50;margin:22px 0}table{width:100%;border-collapse:collapse;margin-top:28px}
    td,th{padding:13px 5px;text-align:left;border-bottom:1px solid #d8dfd9}
    .total{font-weight:bold;background:#eff4ee}.foot{font-size:10px;color:#67776e;margin-top:70px}'''
    with pymupdf.open() as doc:
        page = doc.new_page(width=420, height=550)
        remaining, scale = page.insert_htmlbox(page.rect, html, css=css)
        assert remaining >= 0
        doc.save(root/f'hindi_{variant}.pdf')
        page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(root/f'hindi_{variant}.png')
translations = {
    'marathi': {'काल्पनिक दस्तावेज़ · केवल शोध के लिए':'काल्पनिक दस्तऐवज · केवळ संशोधनासाठी',
        'सहयोग स्टोर':'सहयोग स्टोअर', 'खरीद की रसीद':'खरेदीची पावती', 'रसीद संख्या':'पावती क्रमांक',
        'विवरण':'तपशील', 'राशि (रु.)':'रक्कम (रु.)', 'किताबें':'पुस्तके', 'स्टेशनरी':'लेखनसामग्री',
        'फाइलें':'फाईली', 'कुल राशि':'एकूण रक्कम',
        'यह एक कृत्रिम उदाहरण है। किसी वास्तविक व्यक्ति या दुकान से संबंधित नहीं है।':'हा एक कृत्रिम नमुना आहे. कोणत्याही वास्तविक व्यक्तीशी किंवा दुकानाशी संबंधित नाही.'},
    'tamil': {'काल्पनिक दस्तावेज़ · केवल शोध के लिए':'மாதிரி ஆவணம் · ஆய்வுக்காக மட்டும்',
        'सहयोग स्टोर':'மாதிரி கடை', 'खरीद की रसीद':'விற்பனை ரசீது', 'रसीद संख्या':'ரசீது எண்', 'दिनांक':'தேதி',
        'विवरण':'விவரம்', 'राशि (रु.)':'தொகை (ரூ.)', 'किताबें':'புத்தகங்கள்', 'स्टेशनरी':'எழுதுபொருட்கள்',
        'फाइलें':'கோப்புகள்', 'कुल राशि':'மொத்தத் தொகை',
        'यह एक कृत्रिम उदाहरण है। किसी वास्तविक व्यक्ति या दुकान से संबंधित नहीं है।':'இது ஆய்வுக்கான மாதிரி. உண்மையான நபர் அல்லது கடையுடன் தொடர்பில்லை.'},
    'bengali': {'काल्पनिक दस्तावेज़ · केवल शोध के लिए':'কাল্পনিক নথি · শুধুমাত্র গবেষণার জন্য',
        'सहयोग स्टोर':'সহযোগ স্টোর', 'खरीद की रसीद':'ক্রয়ের রসিদ', 'रसीद संख्या':'রসিদ নম্বর', 'दिनांक':'তারিখ',
        'विवरण':'বিবরণ', 'राशि (रु.)':'রাশি (রু.)', 'किताबें':'বই', 'स्टेशनरी':'লেখার সামগ্রী',
        'फाइलें':'ফাইল', 'कुल राशि':'মোট রাশি',
        'यह एक कृत्रिम उदाहरण है। किसी वास्तविक व्यक्ति या दुकान से संबंधित नहीं है।':'এটি একটি কৃত্রিম উদাহরণ। কোনো প্রকৃত ব্যক্তি বা দোকানের সঙ্গে সম্পর্কিত নয়।'}
}
for language, mapping in translations.items():
    content = html.replace('1,950', '1,250')
    for source, target in mapping.items():
        content = content.replace(source, target)
    with pymupdf.open() as doc:
        page = doc.new_page(width=420, height=550)
        remaining, scale = page.insert_htmlbox(page.rect, content, css=css)
        assert remaining >= 0
        doc.save(root/f'{language}_original.pdf')
        page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(root/f'{language}_original.png')
print(f'Multilingual samples saved in {root}')
