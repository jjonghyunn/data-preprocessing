from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SiteInfo:
    subsidiary: str | None
    country: str | None
    site_code: str          # 입력 받은 site_code (정규화 후)
    rsid: str               # 최종 report suite id

# ✅ 여기에 "정식" 매핑만 넣으면 됨 (언더스코어 포함 버전은 그대로)
_SITE_MASTER: dict[str, tuple[str | None, str | None, str]] = {
    # --- MST ---
    "mstglobal": (None, "MST Global", "company_rsid_mstglobal"),

    # --- SEAU ---
    "au": ("SEAU", "Australia", "company_rsid_au"),
    "bd": ("SIEL", "Bangladesh", "company_rsid_bd"),
    "in": ("SIEL", "India", "company_rsid_in"),
    "id": ("SEIN", "Indonesia", "company_rsid_id"),
    "my": ("SME", "Malaysia", "company_rsid_my"),
    "nz": ("SENZ", "New Zealand", "company_rsid_nz"),
    "ph": ("SEPCO", "Philippines", "company_rsid_ph"),
    "sg": ("SESP", "Singapore", "company_rsid_sg"),
    "th": ("TSE", "Thailand", "company_rsid_th"),
    "vn": ("SAVINA", "Vietnam", "company_rsid_vn"),
    "sec": ("SEC", "Korea", "company_rsid_sec"),
    "mm": ("TSE", "Myanmar", "company_rsid_mm"),
    "jp": ("SEJ", "Japan", "company_rsid_jp"),
    "cn": ("SCIC", "China", "company_rsid_cn"),
    "hk": ("SEHK", "HongKong", "company_rsid_hk"),
    "hk_en": ("SEHK", "HongKong", "company_rsid_hken"),
    "tw": ("SET", "Taiwan", "company_rsid_tw"),
    "az": ("SERC", "Azerbaijan", "company_rsid_az"),
    "kz_ru": ("SECE", "Kazakhstan", "company_rsid_kzru"),
    "kz_kz": ("SECE", "Kazakhstan", "company_rsid_kzkz"),
    "ge": ("SERC", "Georgia", "company_rsid_ge"),
    "mn": ("SECE", "Mongolia", "company_rsid_mn"),
    "ru": ("SERC", "Russia", "company_rsid_ru"),
    "ua": ("SEUC", "Ukraine", "company_rsid_ua"),
    "uz_ru": ("SEUZ", "Uzbekistan", "company_rsid_uzru"),
    "uz_uz": ("SEUZ", "Uzbekistan", "company_rsid_uzuz"),
    "africa_en": ("SCA", "Africa Pan", "company_rsid_africaen"),
    "africa_fr": ("SCA", "Africa Pan", "company_rsid_africafr"),
    "eg": ("SEEG-S", "Egypt", "company_rsid_eg"),
    "iran": ("Iran", "Iran", "company_rsid_iran"),
    "il": ("SEIL", "Israel", "company_rsid_il"),
    "iq_ku": ("SELV", "Kurdistan", "company_rsid_ku"),
    "iq_ar": ("SELV", "Iraq", "company_rsid_iqar"),
    "levant": ("SELV", "Levant", "company_rsid_levant"),
    "levant_ar": ("SELV", "Levant", "company_rsid_levantar"),
    "africa_pt": ("SCA", "Africa Pan", "company_rsid_africapt"),
    "n_africa": ("SEMAG", "North Africa", "company_rsid_nafrica"),
    "pk": ("SEPAK", "Pakistan", "company_rsid_pk"),
    "ps": ("SEIL", "Palestine", "company_rsid_ps"),
    "sa": ("SESAR", "Saudi Arabia", "company_rsid_sa"),
    "tr": ("SETK", "Turkey", "company_rsid_tr"),
    "ae": ("SGE", "UAE", "company_rsid_ae"),
    "ae_ar": ("SGE", "UAE", "company_rsid_aear"),
    "sa_en": ("SESAR", "Saudi Arabia", "company_rsid_saen"),
    "za": ("SSA", "South Africa", "company_rsid_za"),
    "lb": ("SELV", "Lebanon", "company_rsid_lb"),

    # --- Europe etc ---
    "at": ("SEAS", "Austria", "company_rsid_at"),
    "be": ("SEBN", "Belgium", "company_vrs_be"),
    "be_fr": ("SEBN", "Belgium", "company_vrs_be"),
    "ba": ("SEAD", "Bosnia", "company_rsid_ba"),
    "bg": ("SEROM", "Bulgaria", "company_rsid_bg"),
    "hr": ("SEAD", "Croatia", "company_rsid_hr"),
    "cz": ("SECZ", "Czech", "company_rsid_cz"),
    "dk": ("SENA", "Denmark", "company_rsid_dk"),
    "ee": ("SEB", "Estonia", "company_rsid_ee"),
    "fi": ("SENA", "Finland", "company_rsid_fi"),
    "fr": ("SEF", "France", "company_rsid_fr"),
    "de": ("SEG", "Germany", "company_vrs_de"),
    "gr": ("SEGR", "Greece", "company_rsid_gr"),
    "hu": ("SEH", "Hungary", "company_rsid_hu"),
    "ie": ("SEUK", "Ireland", "company_rsid_ie"),
    "it": ("SEI", "Italy", "company_rsid_it"),
    "lv": ("SEB", "Latvia", "company_rsid_lv"),
    "lt": ("SEB", "Lithuania", "company_rsid_lt"),
    "mk": ("SEAD", "Macedonia", "company_rsid_mk"),
    "nl": ("SEBN", "Netherlands", "company_vrs_nl"),
    "no": ("SENA", "Norway", "company_rsid_no"),
    "pl": ("SEPOL", "Poland", "company_rsid_pl"),
    "pt": ("SEIB", "Portugal", "company_vrs_pt"),
    "ro": ("SEROM", "Romania", "company_rsid_ro"),
    "rs": ("SEAD", "Serbia", "company_rsid_rs"),
    "sk": ("SECZ", "Slovakia", "company_rsid_sk"),
    "si": ("SEAD", "Slovenia", "company_rsid_si"),
    "es": ("SEIB", "Spain", "company_vrs_es"),
    "se": ("SENA", "Sweden", "company_rsid_se"),
    "ch": ("SEAS", "Switzerland", "company_rsid_ch"),
    "ch_fr": ("SEAS", "Switzerland-FR", "company_rsid_chfr"),
    "uk": ("SEUK", "United Kingdom", "company_vrs_uk"),
    "al": ("SEAD", "Albania", "company_rsid_al"),

    # --- Americas ---
    "ar": ("SEASA", "Argentina", "company_rsid_ar"),
    "br": ("SEDA", "Brazil", "company_rsid_br"),
    "cl": ("SECH", "Chile", "company_rsid_cl"),
    "co": ("SAMCOL", "Colombia", "company_rsid_co"),
    "latin_en": ("SELA", "Panama", "company_rsid_latinen"),
    "latin": ("SELA", "Panama", "company_rsid_latin"),
    "pe": ("SEPR", "Peru", "company_rsid_pe"),
    "uy": ("SELA", "Uruguay", "company_rsid_uy"),
    "py": ("SELA", "Paraguay", "company_rsid_py"),
    "ca": ("SECA", "Canada", "company_rsid_ca"),
    "ca_fr": ("SECA", "Canada", "company_rsid_cafr"),
    "mx": ("SEM", "Mexico", "company_rsid_mx"),
    "us": ("SEA", "US", "company_rsid_us"),
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
    return SiteInfo(None, None, sc, f"company_rsid_{sc2}")
