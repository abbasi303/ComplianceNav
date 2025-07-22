"""
Real Regulatory Data Sources Configuration
Maps industries and countries to official regulation sources
"""

OFFICIAL_SOURCES = {
    "EU": {
        "eur_lex": {
            "name": "EUR-Lex",
            "base_url": "https://eur-lex.europa.eu",
            "authority": "European Commission",
            "search_endpoint": "/search.html?qid=&text={query}&scope=EURLEX&type=quick&lang=en",
            "direct_access": {
                "GDPR": "/eli/reg/2016/679/oj",
                "ePrivacy": "/eli/dir/2002/58/oj",
                "NIS": "/eli/dir/2016/1148/oj"
            }
        }
    },
    "Germany": {
        "gesetze_im_internet": {
            "name": "Gesetze im Internet", 
            "base_url": "https://www.gesetze-im-internet.de",
            "authority": "German Federal Government",
            "laws": {
                "BDSG": "/bdsg_2018/",
                "TMG": "/tmg/", 
                "KWG": "/kwg/",
                "ZAG": "/zag/",
                "HGB": "/hgb/"
            }
        },
        "bafin": {
            "name": "BaFin",
            "base_url": "https://www.bafin.de",
            "authority": "Federal Financial Supervisory Authority",
            "sectors": {
                "fintech": "/EN/Supervision/FinTech/",
                "payment": "/EN/Supervision/PaymentInstitutions/",
                "banking": "/EN/Supervision/BankingSupervision/"
            }
        }
    }
}

INDUSTRY_REGULATIONS = {
    "healthcare": {
        "EU": ["GDPR", "Medical Device Regulation", "ePrivacy"],
        "Germany": ["BDSG", "Arzneimittelgesetz", "Medizinproduktegesetz"]
    },
    "fintech": {
        "EU": ["PSD2", "GDPR", "MiFID II", "AML Directive"],
        "Germany": ["KWG", "ZAG", "WpHG", "BDSG", "GwG"]
    },
    "technology": {
        "EU": ["GDPR", "ePrivacy", "Digital Services Act"],
        "Germany": ["BDSG", "TMG", "TKG"]
    }
}

REGULATION_URLS = {
    "GDPR": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "BDSG": "https://www.gesetze-im-internet.de/bdsg_2018/",
    "TMG": "https://www.gesetze-im-internet.de/tmg/",
    "PSD2": "https://eur-lex.europa.eu/eli/dir/2015/2366/oj",
    "KWG": "https://www.gesetze-im-internet.de/kwg/",
    "ZAG": "https://www.gesetze-im-internet.de/zag/"
} 