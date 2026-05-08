# site_registry.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SiteInfo:
    subsidiary: str | None
    country: str | None
    site_code: str          # 입력 받은 site_code (정규화 후)
    rsid: str               # 최종 report suite id

# ✅ 여기에 “정식” 매핑만 넣으면 됨 (언더스코어 포함 버전은 그대로)
_SITE_MASTER: dict[str, tuple[str | None, str | None, str]] = {
    # --- MST ---
    "mstglobal": (None, "MST Global", "rsid_placeholder"),

    # --- SEAU ---
    "au": ("SEAU", "Australia", "rsid_placeholder"),
    "bd": ("SIEL", "Bangladesh", "rsid_placeholder"),
    "in": ("SIEL", "India", "rsid_placeholder"),
    "id": ("SEIN", "Indonesia", "rsid_placeholder"),
    "my": ("SME", "Malaysia", "rsid_placeholder"),
    "nz": ("SENZ", "New Zealand", "rsid_placeholder"),
    "ph": ("SEPCO", "Philippines", "rsid_placeholder"),
    "sg": ("SESP", "Singapore", "rsid_placeholder"),
    "th": ("TSE", "Thailand", "rsid_placeholder"),
    "vn": ("SAVINA", "Vietnam", "rsid_placeholder"),
    "sec": ("SEC", "Korea", "rsid_placeholder"),
    "mm": ("TSE", "Myanmar", "rsid_placeholder"),
    "jp": ("SEJ", "Japan", "rsid_placeholder"),
    "cn": ("SCIC", "China", "rsid_placeholder"),
    "hk": ("SEHK", "HongKong", "rsid_placeholder"),
    "hk_en": ("SEHK", "HongKong", "rsid_placeholder"),
    "tw": ("SET", "Taiwan", "rsid_placeholder"),
    "az": ("SERC", "Azerbaijan", "rsid_placeholder"),
    "kz_ru": ("SECE", "Kazakhstan", "rsid_placeholder"),
    "kz_kz": ("SECE", "Kazakhstan", "rsid_placeholder"),
    "ge": ("SERC", "Georgia", "rsid_placeholder"),
    "mn": ("SECE", "Mongolia", "rsid_placeholder"),
    "ru": ("SERC", "Russia", "rsid_placeholder"),
    "ua": ("SEUC", "Ukraine", "rsid_placeholder"),
    "uz_ru": ("SEUZ", "Uzbekistan", "rsid_placeholder"),
    "uz_uz": ("SEUZ", "Uzbekistan", "rsid_placeholder"),
    "africa_en": ("SCA", "Africa Pan", "rsid_placeholder"),
    "africa_fr": ("SCA", "Africa Pan", "rsid_placeholder"),
    "eg": ("SEEG-S", "Egypt", "rsid_placeholder"),
    "iran": ("Iran", "Iran", "rsid_placeholder"),
    "il": ("SEIL", "Israel", "rsid_placeholder"),
    "iq_ku": ("SELV", "Kurdistan", "rsid_placeholder"),
    "iq_ar": ("SELV", "Iraq", "rsid_placeholder"),
    "levant": ("SELV", "Levant", "rsid_placeholder"),
    "levant_ar": ("SELV", "Levant", "rsid_placeholder"),
    "africa_pt": ("SCA", "Africa Pan", "rsid_placeholder"),
    "n_africa": ("SEMAG", "North Africa", "rsid_placeholder"),
    "pk": ("SEPAK", "Pakistan", "rsid_placeholder"),
    "ps": ("SEIL", "Palestine", "rsid_placeholder"),
    "sa": ("SESAR", "Saudi Arabia", "rsid_placeholder"),
    "tr": ("SETK", "Turkey", "rsid_placeholder"),
    "ae": ("SGE", "UAE", "rsid_placeholder"),
    "ae_ar": ("SGE", "UAE", "rsid_placeholder"),
    "sa_en": ("SESAR", "Saudi Arabia", "rsid_placeholder"),
    "za": ("SSA", "South Africa", "rsid_placeholder"),
    "lb": ("SELV", "Lebanon", "rsid_placeholder"),

    # --- Europe etc ---
    "at": ("SEAS", "Austria", "rsid_placeholder"),
    "be": ("SEBN", "Belgium", "rsid_placeholder"),
    "be_fr": ("SEBN", "Belgium", "rsid_placeholder"),  # (표가 be/be_fr 같이 적혀있어서 일단 동일 RSID로 둠)
    "ba": ("SEAD", "Bosnia", "rsid_placeholder"),
    "bg": ("SEROM", "Bulgaria", "rsid_placeholder"),
    "hr": ("SEAD", "Croatia", "rsid_placeholder"),
    "cz": ("SECZ", "Czech", "rsid_placeholder"),
    "dk": ("SENA", "Denmark", "rsid_placeholder"),
    "ee": ("SEB", "Estonia", "rsid_placeholder"),
    "fi": ("SENA", "Finland", "rsid_placeholder"),
    "fr": ("SEF", "France", "rsid_placeholder"),
    "de": ("SEG", "Germany", "rsid_placeholder"),
    "gr": ("SEGR", "Greece", "rsid_placeholder"),
    "hu": ("SEH", "Hungary", "rsid_placeholder"),
    "ie": ("SEUK", "Ireland", "rsid_placeholder"),
    "it": ("SEI", "Italy", "rsid_placeholder"),
    "lv": ("SEB", "Latvia", "rsid_placeholder"),
    "lt": ("SEB", "Lithuania", "rsid_placeholder"),
    "mk": ("SEAD", "Macedonia", "rsid_placeholder"),
    "nl": ("SEBN", "Netherlands", "rsid_placeholder"),
    "no": ("SENA", "Norway", "rsid_placeholder"),
    "pl": ("SEPOL", "Poland", "rsid_placeholder"),
    "pt": ("SEIB", "Portugal", "rsid_placeholder"),
    "ro": ("SEROM", "Romania", "rsid_placeholder"),
    "rs": ("SEAD", "Serbia", "rsid_placeholder"),
    "sk": ("SECZ", "Slovakia", "rsid_placeholder"),
    "si": ("SEAD", "Slovenia", "rsid_placeholder"),
    "es": ("SEIB", "Spain", "rsid_placeholder"),
    "se": ("SENA", "Sweden", "rsid_placeholder"),
    "ch": ("SEAS", "Switzerland", "rsid_placeholder"),
    "ch_fr": ("SEAS", "Switzerland-FR", "rsid_placeholder"),
    "uk": ("SEUK", "United Kingdom", "rsid_placeholder"),
    "al": ("SEAD", "Albania", "rsid_placeholder"),

    # --- Americas ---
    "ar": ("SEASA", "Argentina", "rsid_placeholder"),
    "br": ("SEDA", "Brazil", "rsid_placeholder"),
    "cl": ("SECH", "Chile", "rsid_placeholder"),
    "co": ("SAMCOL", "Colombia", "rsid_placeholder"),
    "latin_en": ("SELA", "Panama", "rsid_placeholder"),
    "latin": ("SELA", "Panama", "rsid_placeholder"),
    "pe": ("SEPR", "Peru", "rsid_placeholder"),
    "uy": ("SELA", "Uruguay", "rsid_placeholder"),
    "py": ("SELA", "Paraguay", "rsid_placeholder"),
    "ca": ("SECA", "Canada", "rsid_placeholder"),
    "ca_fr": ("SECA", "Canada", "rsid_placeholder"),  
    "mx": ("SEM", "Mexico", "rsid_placeholder"),
    "us": ("SEA", "US", "rsid_placeholder"),
}

def lookup_site(site_code: str) -> SiteInfo:
    sc = str(site_code).strip().lower()
    sc2 = sc.replace("_", "")  # alias

    # 1) 정식키 우선 (ca_fr)
    if sc in _SITE_MASTER:
        sub, country, rsid = _SITE_MASTER[sc]
        return SiteInfo(sub, country, sc, rsid)

    # 2) '_' 제거 alias (cafr)
    if sc2 in _SITE_MASTER:
        sub, country, rsid = _SITE_MASTER[sc2]
        return SiteInfo(sub, country, sc, rsid)

    # 3) 마스터에 없으면 fallback(그래도 '_' 제거 규칙)
    return SiteInfo(None, None, sc, f"sscompany_name4{sc2}")
