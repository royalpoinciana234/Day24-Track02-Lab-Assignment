# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.predefined_recognizers import EmailRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

def build_vietnamese_analyzer() -> AnalyzerEngine:

    # --- TASK 2.2.1 ---
    # CCCD: 12 chữ số, dùng lookahead/lookbehind thay vì \b để tránh lỗi standalone string
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"(?<!\d)\d{12}(?!\d)",
        score=0.9
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[cccd_pattern],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # --- TASK 2.2.2 ---
    # SĐT VN: 0[35789]xxxxxxxx
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_phone",
            regex=r"(?<!\d)0[35789]\d{8}(?!\d)",
            score=0.85
        )],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    # Tên người Việt: 2-4 từ viết hoa (họ + đệm + tên)
    # VD: "Nguyễn Văn A", "Trần Thị Bích Ngọc"
    vn_name_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_name",
            regex=r"\b[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠẮẶẦẤẬẢẰỆẾỄỔỘỢỚỜỞỤỮỰỰỨỪ][a-zàáâãèéêìíòóôõùúăđĩũơưạắặầấậảằệếễổộợớờởụữựựứừ]+"
                  r"(?:\s[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯẠẮẶẦẤẬẢẰỆẾỄỔỘỢỚỜỞỤỮỰỰỨỪ][a-zàáâãèéêìíòóôõùúăđĩũơưạắặầấậảằệếễổộợớờởụữựựứừ]+){1,3}\b",
            score=0.6
        )],
        context=["bệnh nhân", "họ tên", "ho_ten", "tên", "bác sĩ"]
    )

    # --- TASK 2.2.3 ---
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "vi",
                    "model_name": "vi_core_news_lg"}]
    })
    nlp_engine = provider.create_engine()

    # --- TASK 2.2.4 ---
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(EmailRecognizer(supported_language="vi"))
    analyzer.registry.add_recognizer(vn_name_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
    return results
