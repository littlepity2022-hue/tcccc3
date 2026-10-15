from datetime import datetime
from io import BytesIO
import pandas as pd
import streamlit as st

# ==========================================
# 網頁基本設定
# ==========================================
st.set_page_config(
    page_title="化療藥物作業流程與物資請領系統", layout="centered", page_icon="🏥"
)

# --- CSS 樣式優化 ---
st.markdown(
    """
    <style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 定義側邊欄導覽
# ==========================================
with st.sidebar:
  st.title("⚙️ 功能選單")

  # 新增「📦 醫療物資請領清單」主選項
  page = st.radio(
      "請選擇功能單元：",
      [
          "📌 平日審核藥師工作事項",
          "⚡ 週六單人流程核心",
          "📋 SOP 作業流程查檢",
          "📦 醫療物資請領清單",
      ],
  )

  st.divider()

  if page == "📋 SOP 作業流程查檢":
    role = st.radio(
        "請選擇您的操作角色：", ["💊 調配藥師", "👨‍⚕️ 審核藥師"], index=0
    )
    st.info("切換角色後，下方的待辦進度將會重新計算。")

# ==========================================
# 角色 A：調配藥師資料庫
# ==========================================
prep_data = {
    "1. 前置作業": {
        "步驟": [
            "1.1 進入化療室之前，需先關閉UV燈。",
            "1.2 設定當日化療標籤貼紙上列印的藥師。",
            (
                "1.3 打開無菌通風開關，打開生物安全櫃開關 (至少使用前30分鐘開機運轉)。"
            ),
            "1.4 登記化療調配室的溫濕度、生物操作檯數據、壓差表。",
            "1.5 開啟當日作業所需的化療系統。",
            "1.5 將漏液機裝上管線並進行校正 (每次100ml)。",
            (
                "1.6 調配前後皆須以紗布沾溼75％酒精進行清潔"
                " (由上而下、由內而外)。"
            ),
        ],
        "注意事項": (
            "環境濕度與溫度監控標準為溫度20-25℃、溼度40-70%。調配室內環境應為負壓(-2.5Pa或更低)。"
        ),
    },
    "2. 處方核對": {
        "步驟": [
            "2.1 確認化療醫囑開立完成後，自動列印化療處方評估單。",
            "2.2 依據處方評估單上的檢驗數值進行審核 (可同步查詢癌症治療計畫書)。",
            "2.3 處方評誤無誤後，完成審核確認，等待化療標籤列印。",
        ],
        "注意事項": (
            "處方有任何疑義須立即連絡醫囑端。門診病人須等待批價完成，並由護理人員將處方箋送至調配室後才開始調配。"
        ),
    },
    "3. 備藥": {
        "步驟": [
            "2.4 門診化療前置藥依藥袋進行調劑。",
            "3.1 將一式兩份的化療標籤貼紙各自黏貼在點滴及避光袋上。",
            "3.2 備藥時，以一藥一籃區分 (門診紅籃、住院白籃、非當日藍籃)。",
            "3.3 備藥藥師將特殊保存藥品(冷藏、避光、不需過濾管線)畫紅圈標記。",
        ],
        "注意事項": (
            "藥品調配以門診病人優先。備藥籃拿至儲盒旁才可拿取藥品，藥品須於備藥籃内拆除包裝。"
        ),
    },
    "4. 調配前置作業": {
        "步驟": [
            "3.4 依照醫囑開立的稀釋液體積來決定是否漏液。",
            "3.5 備藥完成後經由 PASS BOX 送至化療調配室進行調配。",
            (
                "4.1 進入緩衝室著裝：穿鞋套 → 戴隔離帽 → 戴口罩(外科/N95) →"
                " 穿內層隔離衣 → 洗手30秒擦乾 → 戴第一層手套 → 穿外層隔離衣"
                " → 戴第二層手套。"
            ),
            (
                "4.2 每日操作前，需在生物安全櫃檯面鋪上單面防水吸水墊，再放入器具。"
            ),
        ],
        "注意事項": (
            "調配體積若超過原點滴10%容積，則請醫囑修正點滴容積。生物安全櫃前方拉門應拉至適當位置保護臉部和眼睛。"
        ),
    },
    "5. 調配藥品": {
        "步驟": [
            (
                "5.1"
                " 調配化療藥品時，須完成一個藥品才進行下一輪作業，嚴禁同時配製多項。"
            ),
            (
                "5.2 執行三讀五對 (一讀標籤/藥品、二讀病人資料/劑量、三讀空瓶/標籤；五對:適應症/劑量/稀釋液/流速/途徑)。"
            ),
            "5.3 由審核藥師進行化療藥抽取量的覆核。",
            "5.4 調配結束後，脫掉第二層(外層)手套後離開生物安全櫃。",
        ],
        "注意事項": (
            "卸裝步驟：脫掉隔離帽→口罩→鞋套→隔離衣→內層手套→密封丟棄於化療垃圾袋→洗手。每日結束後關閉操作台並打開UV燈。"
        ),
    },
    "6. 藥物封包 & 7. 運輸藥品": {
        "步驟": [
            "6.1 門診化療藥物進行秤重稽核(5%內)，內外袋比對後封包。",
            "6.2 住院化療藥物經由 PASS BOX 送至化療準備室進行核發及封包。",
            "6.3 系統進行化療發藥作業 (刷取條碼、系統記錄秤重量)。",
            "7.1 封包完成後，系統派單傳送，等待領取。",
            "7.2 傳送人員領取時，須登入化療傳送系統刷取簽收。",
        ],
        "注意事項": (
            "避光袋封口兩次，以最少空間密封避免擠壓滲漏。化療須以專用傳送車運送(隨車備有潑灑箱)。"
        ),
    },
    "8. 例行性業務": {
        "步驟": [
            "8.1 每月做落菌試驗 (培養皿放置生物安全櫃一小時)。",
            "8.2 每週一進行耗材請領。",
            "8.3 遇缺藥時進行緊急請領。",
            (
                "8.4"
                " 每週六進行環境清潔"
                " (75%酒精擦拭、更換防塵墊、處理細胞毒性廢棄物)。"
            ),
            "8.5 每週三下午進行藥物盤點。",
            "8.6 每週二、五進行藥物撥補。",
            "8.7 每週六至供應中心領回消毒後的手術衣與無菌治療巾。",
            "8.8 每月10日前完成業務量統計。",
        ],
        "注意事項": (
            "細胞毒性廢棄物需依規定處理，外側貼上基因毒性廢棄物專用貼紙。"
        ),
    },
    "9. 潑灑與 10. 針扎處理": {
        "步驟": [
            (
                "9.1 [櫃內潑灑]"
                " 脫掉受污染衣物，穿上乾淨裝備，以紗布/吸水巾吸收藥液，75%酒精擦拭至少三遍。"
            ),
            (
                "9.2 [櫃外潑灑]"
                " 穿戴防護裝備，標示區域禁止靠近，以同心圓由外向內清潔，75%酒精擦拭三遍。"
            ),
            (
                "10.1 [針扎處理]"
                " 不馬上拔針，倒抽柱塞抽出藥品。拔針脫手套，擠出血液，大量流動清水沖洗傷口5分鐘。"
            ),
            "10.2 報備單位主管，並進系統完成安全通報(針扎事件)。",
        ],
        "注意事項": (
            "若潑灑大於5mL或5gm，應立即使用抗污紙巾覆蓋。若接觸皮膚/眼睛，應以大量清水沖洗至少15分鐘後送醫。"
        ),
    },
}

# ==========================================
# 角色 B：審核藥師資料庫
# ==========================================
audit_data = {
    "1. 準備工作": {
        "步驟": [
            "1.1 關閉 UV 燈開關，開啟無菌無塵操作檯並完成調劑前準備工作。",
            "1.2 每日登記化療調配室溫濕度、生物操作台數據。",
            "1.3 打開化療系統。",
        ],
        "注意事項": (
            "• 操作台至少在使用前 30 分鐘開啟。\n• UV 燈開關下班時開啟。\n•"
            " 確認印表機正常作業。"
        ),
    },
    "2. 處方核對": {
        "步驟": [
            (
                "2.1"
                " 處方評估單於醫囑開立後自動列印，藥師依據相關檢驗值及治療計畫進行審核。(His"
                " 5 化療處方)"
            ),
            "2.2 門診化療須依化療門診處方箋來進行領取化療藥品。",
            "2.3 門診化療前置藥依藥袋進行調劑。(His 5 化療前置藥調劑)",
        ],
        "注意事項": (
            "• 可由 HIS 5 化療處方之「癌症專區」查看治療計畫書。\n•"
            " 處方有疑義須聯絡醫囑端，並後續進行記錄。\n•"
            " 領取藥品須以條碼刷取及針劑比對方式進行。\n•"
            " 前置藥完成後傳遞到調配室，進行核發給化療注射室。"
        ),
    },
    "3. 化療藥物之調配準備": {
        "步驟": [
            "3.1 化療處方審核確認後，將化療標籤貼紙同步貼在點滴及避光袋上。",
            "3.2 依據處方進行備藥 (His 5 化療處方調劑)。",
            (
                "3.3 以籃子進行區分，門診放置紅籃，住院放置白籃，非當日的住院療程則放置於藍色籃子。"
            ),
            "3.4 備藥完成後，送至調配室。",
        ],
        "注意事項": (
            "• 審核確認後，一式兩聯的化療標籤貼紙會自動列印。藥品調配以門診為優先。\n•"
            " 藥品及點滴皆須以條碼刷取進行系統比對並秤重。\n•"
            " 一個藥品放置一個籃子。\n• 門診化療超過 10"
            " 籃時，以處方開立順序給予號碼牌，冰箱藥給予相對應的號碼後冷藏。\n•"
            " 備藥完成後經由 PASS BOX 運送。"
        ),
    },
    "4. 化療調配之雙人覆核": {
        "步驟": ["4.1 確認調配過程中，抽取藥液的體積正確。"],
        "注意事項": "• 以對講機及監視螢幕進行覆核。",
    },
    "5. 藥物之運送": {
        "步驟": [
            "5.1 住院化療調配完成後，由調配藥師送出。",
            (
                "5.2"
                " 核對藥師進行封包及核發，經由條碼刷取內外袋標籤進行發藥."
                " 系統自動派送給傳送人員進行運送。(His 5 化療處方發藥)"
            ),
        ],
        "注意事項": (
            "• 調配完成後經由 PASS BOX 運送。\n•"
            " 系統自動通知傳送，由傳送人員以化療專用推車進行簽收運送。(His"
            " 5 化療傳送)"
        ),
    },
    "6. 提供相關之藥物諮詢": {
        "步驟": ["6.1 回覆化療相關之諮詢電話。"],
        "注意事項": "",
    },
    "7. 相關業務 & 8. 其他": {
        "步驟": ["7.1 參照化療藥物調配藥師工作規定 7。", "8.1 完成主管交辦事項。"],
        "注意事項": "",
    },
}

# ==========================================
# 醫療物資請領系統：各分頁資料定義
# ==========================================
items_data_page1_stock = [
    ("庫存品", "M6CEE010038", "愛喜優克萊福藥物準備系統組件-輸液管轉接頭"),
    ("庫存品", "M6CEE010049", "普惠靜注延長管-T型"),
    ("庫存品", "M6NAN010075", "注射針/Sterican 18G"),
    ("庫存品", "M6W0C010003", "治療紙巾(抗汗紙卷)"),
    ("庫存品", "M6W0C020079", "外科手術口罩(醫療口罩)"),
    ("庫存品", "M6W0C020133", "舜堡外科手術用口罩-N95"),
    ("庫存品", "M6W0C030006", "紙帽/shanluen\\不織布, 圓形"),
    ("庫存品", "M6W1F010166", "中衛鞋套(未滅菌)"),
    ("庫存品", "M6W7ST10040", "無粉多倍乳膠健檢手套 L"),
    ("庫存品", "M6W7ST10041", "無粉多倍乳膠健檢手套 M"),
    ("庫存品", "M6W7ST10042", "無粉多倍乳膠健檢手套 S"),
    ("庫存品", "M6W7ST10096", "華新手術手套(無粉)(滅菌/未滅菌) 無粉, #6.0"),
    ("庫存品", "M6W7ST10097", "華新手術手套(無粉)(滅菌/未滅菌) 無粉, #6.5"),
    ("庫存品", "M6W7ST10098", "華新手術手套(無粉)(滅菌/未滅菌) 無粉, #7.0"),
    ("庫存品", "M6W7ST10099", "華新手術手套(無粉)(滅菌/未滅菌) 無粉, #7.5"),
    ("庫存品", "M6W7ST10100", "華新手術手套(無粉)(滅菌/未滅菌) 無粉, #8.0"),
    ("庫存品", "M6W7ST10101", "華新手術手套(無粉)(滅菌/未滅菌) 無粉, #8.5"),
    ("庫存品", "M6W9A010009", "滅菌防塵墊(地板藍色)"),
    ("庫存品", "M6W9A010074", "保盾拋棄式醫用衣物-隔離衣(潑灑箱用)"),
    ("庫存品", "M6W9A050024", "護目鏡-輕便型"),
    ("庫存品", "M6W9A070045", "基因毒性廢棄物收集桶(22公升)"),
    ("庫存品", "M6WDD010009", "大紗布，10片/包"),
    ("庫存品", "M6WDD010041", "酒精棉片"),
    ("庫存品", "M6W9A010007", "Surgical Gown 保盾一次性使用手術衣(抽藥外衣)"),
]

items_data_page1_single = [
    ("單一品項", "M600RB00034", "Parafilm M"),
    ("單一品項", "M6E01001532", "凱普森液體轉換管組KAPSAM FLUID TRANSFER TUBE SET"),
    ("單一品項", "M6NAN010089", "SOL-CARE safety needle(25G皮下針頭)"),
    ("單一品項", "M6NBS010010", "塑膠注射筒Syringe 3cc"),
    ("單一品項", "M6NBS010011", "塑膠注射筒Syringe 5cc"),
    ("單一品項", "M6NBS010012", "塑膠注射筒Syringe 10cc"),
    ("單一品項", "M6NBS010014", "塑膠注射筒Syringe 30cc"),
    ("單一品項", "M6NBS010043", "康德萊一次性使用無菌注射器-螺旋式空針 50 cc"),
    ("單一品項", "M6NCS010030", "塑膠注射筒Syringe 1cc"),
    ("單一品項", "M6W7ST10061", "康德樂無粉手術用手套(滅菌)-化療用 #6"),
    ("單一品項", "M6W7ST10062", "康德樂無粉手術用手套(滅菌)-化療用 #6.5"),
    ("單一品項", "M6W7ST10063", "康德樂無粉手術用手套(滅菌)-化療用 #7"),
    ("單一品項", "M6W7ST10064", "康德樂無粉手術用手套(滅菌)-化療用 #7.5"),
    ("單一品項", "M6W7ST10065", "康德樂無粉手術用手套(滅菌)-化療用 #8"),
    ("單一品項", "M6W7ST10072", "康德樂無粉手術用手套(滅菌)-化療用 #8.5"),
    ("單一品項", "M6CLPA20003", "LV10,1Day Infusor,10ml/h奶瓶"),
    ("單一品項", "M6CLPA20004", "LV5,2Day Infusor,5ml/h奶瓶"),
]

items_data_page2 = [
    (
        "調撥領用西藥",
        "庫存品",
        "CSTER03",
        "Disterile Water(支) 20ml/amp(Water for inj)",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CDIST01",
        "Disterile Water(支) 20ml/amp(Water for inj)",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CNS01",
        "0.9% Saline(支) 20ml/amp(Sodium Chloride)",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CSALI08",
        "Sodium Chloride (小) 0.9%,100ml/軟袋(Saline Injection)",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CSALI05",
        "0.9% Saline(小) 250ml/bag(Sodium Chloride),軟袋",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CSALI02",
        "0.9% Sodium Chloride(中) 500ml/軟袋",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CSALI10",
        "0.9% Sodium Chloride (大) 1000mL/軟袋",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CGITO01",
        "5% Dextrose(小) 250ml/bag(Gitose)",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CGITO04",
        "5% Dextrose(大) 500ml/bag(Gitose)",
    ),
    ("調撥領用西藥", "庫存品", "WKESP02", "克司博75%酒精液4000ml/瓶"),
    (
        "調撥領用西藥",
        "庫存品",
        "WANTIG03",
        "Antigerm抑平菌殺菌液(紅色洗手液)",
    ),
    (
        "調撥領用西藥",
        "庫存品",
        "CHAFO01",
        "Haforman Injection 500ml/bag(L-Ringer)",
    ),
]

items_data_page3 = [
    (
        "一般品項",
        "一般品",
        "VA100001161",
        "影印紙 A5/1箱10包(請領單位為包)",
    ),
    ("一般品項", "一般品", "VB071200002", "10號夾鍊袋"),
    ("一般品項", "一般品", "VB071200005", "7號夾鍊袋"),
    ("一般品項", "一般品", "VB225401002", "珍珠洗手液"),
    ("一般品項", "一般品", "VB401304016", "細胞毒性藥物避光袋"),
    ("一般品項", "一般品", "VE9R22A0552", "化療藥品標籤貼紙(白底11.8*17.6cm)"),
]

items_data_page4 = [
    (
        "盤點撥補ZZ",
        "醫材庫存品",
        "VB401304111",
        "感染性垃圾袋-紅、特大(86*87，25個/折=1.14KG)",
    ),
    (
        "盤點撥補ZZ",
        "醫材庫存品",
        "VB401304113",
        "感染性垃圾袋-紅、特小(40*49，50個/折=0.424KG)",
    ),
    ("盤點撥補ZZ", "醫材庫存品", "VE9A29A1155", "基因毒性廢棄物標示貼紙(小)"),
]


# ==========================================
# 介面渲染邏輯
# ==========================================

# 1. SOP 作業流程查檢
if page == "📋 SOP 作業流程查檢":
  if role == "💊 調配藥師":
    st.title("🏥 藥劑科：化學藥物【調配室】作業流程")
    current_data = prep_data
    prefix = "prep"
  else:
    st.title("👨‍⚕️ 藥劑科：化療藥物【審核藥師】作業流程")
    current_data = audit_data
    prefix = "audit"

  st.markdown(f"目前身分：**{role}**，請點選工作項目開始執行。")

  task_options = list(current_data.keys())
  selected_task = st.selectbox(
      "📂 請選擇目前工作項目：", task_options, key=f"{prefix}_task_select"
  )

  st.divider()

  if current_data[selected_task].get("注意事項"):
    st.info(f"**⚠️ 注意事項：**\n\n{current_data[selected_task]['注意事項']}")

  st.subheader(f"📋 {selected_task} - 步驟清單")

  steps = current_data[selected_task]["步驟"]
  checked_count = 0

  for i, step in enumerate(steps):
    is_checked = st.checkbox(step, key=f"{prefix}_{selected_task}_step_{i}")
    if is_checked:
      checked_count += 1

  st.write("---")
  progress = int((checked_count / len(steps)) * 100) if len(steps) > 0 else 0
  st.progress(progress, text=f"此項目完成進度: {progress}%")

  if progress == 100:
    st.success(f"🎉 【{selected_task}】的所有步驟已完成！")

  if role == "💊 調配藥師":
    st.caption("📄 參考文件：化學藥物調配室作業規定 (GTBABC304)")
  else:
    st.caption("📄 參考文件：化療藥物審核藥師工作規定 (GTBABC)")

# 2. 平日審核藥師工作事項
elif page == "📌 平日審核藥師工作事項":
  st.title("📌 審核藥師 工作 Checklist")
  st.markdown("請點開下方各項待辦分類進行勾選核對：")
  st.divider()

  with st.expander("☀️ 每日完成事項", expanded=True):
    st.checkbox("0. 星期一早上裝新的漏液體管子並漏液3次、1次100cc")
    st.caption(
        "Baxa轉接管組一個箱子、T型延長管與輸液管轉接頭在同一箱子，門外靠牆右側上方，裝好後須包parafilm"
    )
    st.checkbox("1. 關閉牆上UV燈(非生物操作台的室外一盞、室內一盞)")
    st.checkbox("2.打開審核電腦和刷藥物電腦、打開生物操作台兩台")
    st.checkbox("3.對磅秤按下break 看到ready字樣按下print")
    st.checkbox("4.打開his 登入打開發藥 多開一個給調配藥師")
    st.checkbox("5.審核藥物 ok後準備bag 漏液 備藥完丟pass box")
    st.caption(
        "↳標籤紙大小必須修剪，100cc剪四邊，250cc剪上下兩刀，門診有剪要加蓋兩個藥師章"
    )
    st.caption(":red[避光]、:red[冷藏]、:red[不可使用過濾器] 需紅筆圈選")
    st.checkbox("6. 登記壓差(審核藥師)", key="chk_d_1")
    st.checkbox(
        "a. 統計每日病人數於月曆 (含療程數量及當日標籤列印人數確認)", key="chk_d_2"
    )
    st.caption(
        "(0+0+0)門診 第一個0是延後配，例如早上配的隔日門診療程，"
        "第二個0是預配但門診沒有預配 ，第三個0是當日配門診"
    )
    st.caption(
        "(0+0+0)住院 第一個0是延後配，例如早上配的今早的QD(已過點)，第二個0是預配:如下午開明日早的QD，第三個0是當日的住院"
    )
    st.checkbox("b. 統計各時段處方量、登記於 Excel", key="chk_d_3")
    st.caption("↳ 步驟打開桌面捷徑115年化療各時段處方量統計")
    st.checkbox("c. 匯出當日工作量 Excel (另存新檔)", key="chk_d_4")
    st.caption(
        "↳"
        " 步驟"
        " HIS系統=>藥局管理=>共用服務=>報表=>化療業務量=>點選xls=>輸出"
        " Excel 並另存於=>每月所需=>工作量=>115年=>當月"
    )
    st.checkbox("d. 補充點滴", key="chk_d_5")
    st.checkbox("e. 倒垃圾", key="chk_d_6")
    st.checkbox("f. 關電腦、電子磅秤、漏液機、監視器螢幕", key="chk_d_7")
    st.checkbox("g. 撕新一層保潔墊、關傳送電腦/電燈、開紫消燈", key="chk_d_8")

  with st.expander("📅 每月完成事項 (電子檔 - 3號前交宛怡)"):
    st.checkbox("115年化療處方near miss.xls", key="chk_m_e_1")
    st.checkbox("115年化療各時段處方量統計.xls", key="chk_m_e_2")
    st.checkbox("1150901-1150931業務量.xls", key="chk_m_e_3")
    st.checkbox(
        "11509化療調配支援紀錄表.pdf (紙本帶去臨床辦公室掃描)", key="chk_m_e_4"
    )
    st.checkbox("115年第四季(10-12)化療室統計資料.pdf", key="chk_m_e_5")
    st.checkbox("115年化療調劑總筆數.xls", key="chk_m_e_6")

  with st.expander("📄 每月完成事項 (紙本 - 月底最後一天交宛怡)"):
    st.checkbox("1. 溫濕度記錄表、壓差記錄表", key="chk_m_p_1")
    st.checkbox("2. 保養卡*2 (生物操作櫃*2、洗眼機、自動藥液分裝機)", key="chk_m_p_2")
    st.checkbox("3. 冰箱溫度異常警鳴測試表", key="chk_m_p_3")
    st.checkbox("4. 安全衛生自動檢查表", key="chk_m_p_4")
    st.checkbox("5. 交班本", key="chk_m_p_5")
    st.checkbox("6. 盤點表、盤點報告、大德捐 (最晚最後一週週五交出)", key="chk_m_p_6")
    st.checkbox("7. PCA 報廢單 (to 雅蓁)", key="chk_m_p_7")

  with st.expander("🔄 每月例行公事"):
    st.checkbox("1. 處方箋、注射卡歸檔滿了箱交藥庫", key="chk_m_r_1")
    st.checkbox("2. 更新下個月需用表單", key="chk_m_r_2")
    st.checkbox("3. 每月完成 5S 及效期查核 (僅審核藥師執行)", key="chk_m_r_3")

# 3. 週六單人流程核心
elif page == "⚡ 週六單人流程核心":
  st.title("⚡ 週六單人流程核心")
  st.markdown("請依照步驟依序進行勾選核對：")
  st.divider()

  sat_steps = [
      "1 關閉牆上UV燈(非生物操作台的室外一盞、室內一盞)",
      "2 打開審核電腦和刷藥物電腦",
      "3 對磅秤按下break 看到ready字樣按下print",
      "4 打開his 登入打開發藥 多開一個給調配藥師",
      "5 審核藥物 ok後準備bag 漏液 備藥後打給4027請線上主管指派人員核對",
      (
          "6"
          " 通常最後一批會等到11:15左右入內開始調配在此之前須完成審核與雙人核對"
      ),
      "7 進入抽藥，清掃完畢可打給3850預約傳送時間",
      "8 發藥、封包、等傳送、登載每日業務報表",
      "9 拆漏液機管線到紅色袋子",
      "10拿下冰箱上的所有表單進行檢查登記",
      "11 收拾、關機關燈開UV燈簽退",
  ]

  checked_sat_count = 0

  for i, step in enumerate(sat_steps):
    if st.checkbox(step, key=f"perfect_sat_step_{i} "):
      checked_sat_count += 1

  st.write("---")
  sat_progress = int((checked_sat_count / len(sat_steps)) * 100)
  st.progress(sat_progress, text=f"流程核對進度: {sat_progress}%")

  if sat_progress == 100:
    st.success("🎉 週六單人流程核心步驟已全部核對完成！")

# 4. 醫療物資請領清單 (完整 5 分頁系統)
elif page == "📦 醫療物資請領清單":
  st.title("📦 醫療物資請領清單登記系統")
  st.write(
      "請在下方各分頁中勾選您需要請領的物品，系統將自動在下方產生完整清單。"
  )

  # 建立 5 個分頁
  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "盤點(庫存品)",
      "盤點(單一品項)",
      "調撥領用西藥 (出庫請點441 請領點541)",
      "一般品項",
      "盤點撥補ZZ",
  ])

  # --- 共用匯出 Excel 函式 ---
  def get_excel_download_button(df, filename_prefix):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df.to_excel(writer, index=False, header=False, sheet_name="請領清單")
    excel_data = output.getvalue()
    return st.download_button(
        label="📥 下載此清單 Excel 檔",
        data=excel_data,
        file_name=f"請領清單_{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )

  # --- 分頁 1：盤點(庫存品) ---
  with tab1:
    st.subheader("📦 盤點撥補醫材 (庫存品) - 勾選區")
    selected_records_p1 = []
    cols = st.columns(2)
    for i, (source, code, name) in enumerate(items_data_page1_stock):
      with cols[i % 2]:
        if st.checkbox(name, key=f"p1_stock_{i}"):
          selected_records_p1.append(("盤點撥補醫材", source, code, name))

    st.markdown("---")
    st.subheader("📋 盤點(庫存品)產生的清單")
    if selected_records_p1:
      df_p1 = pd.DataFrame(selected_records_p1)
      st.dataframe(df_p1, use_container_width=True, hide_index=True)
      get_excel_download_button(df_p1, "盤點_庫存品")
    else:
      st.info("👆 請在上方勾選項目。")

  # --- 分頁 2：盤點(單一品項) ---
  with tab2:
    st.subheader("📦 盤點撥補醫材 (單一品項) - 勾選區")
    selected_records_p2 = []
    cols = st.columns(2)
    for i, (source, code, name) in enumerate(items_data_page1_single):
      with cols[i % 2]:
        if st.checkbox(name, key=f"p1_single_{i}"):
          selected_records_p2.append(("盤點撥補醫材", source, code, name))

    st.markdown("---")
    st.subheader("📋 盤點(單一品項)產生的清單")
    if selected_records_p2:
      df_p2 = pd.DataFrame(selected_records_p2)
      st.dataframe(df_p2, use_container_width=True, hide_index=True)
      get_excel_download_button(df_p2, "盤點_單一品項")
    else:
      st.info("👆 請在上方勾選項目。")

  # --- 分頁 3：調撥領用西藥 ---
  with tab3:
    st.subheader("💊 調撥領用西藥 (出庫請點441 請領點541) - 勾選區")
    selected_records_p3 = []
    cols = st.columns(2)
    for i, (col1_val, col2_val, code, name) in enumerate(items_data_page2):
      with cols[i % 2]:
        if st.checkbox(name, key=f"p2_item_{i}"):
          selected_records_p3.append((col1_val, col2_val, code, name))

    st.markdown("---")
    st.subheader("📋 調撥領用西藥產生的清單")
    if selected_records_p3:
      df_p3 = pd.DataFrame(selected_records_p3)
      st.dataframe(df_p3, use_container_width=True, hide_index=True)
      get_excel_download_button(df_p3, "調撥領用西藥")
    else:
      st.info("👆 請在上方勾選項目。")

  # --- 分頁 4：一般品項 ---
  with tab4:
    st.subheader("📄 一般品項 - 勾選區")
    selected_records_p4 = []
    cols = st.columns(2)
    for i, (col1_val, col2_val, code, name) in enumerate(items_data_page3):
      with cols[i % 2]:
        if st.checkbox(name, key=f"p3_item_{i}"):
          selected_records_p4.append((col1_val, col2_val, code, name))

    st.markdown("---")
    st.subheader("📋 一般品項產生的清單")
    if selected_records_p4:
      df_p4 = pd.DataFrame(selected_records_p4)
      st.dataframe(df_p4, use_container_width=True, hide_index=True)
      get_excel_download_button(df_p4, "一般品項")
    else:
      st.info("👆 請在上方勾選項目。")

  # --- 分頁 5：盤點撥補ZZ ---
  with tab5:
    st.subheader("🗑️ 盤點撥補ZZ - 勾選區")
    selected_records_p5 = []
    cols = st.columns(2)
    for i, (col1_val, col2_val, code, name) in enumerate(items_data_page4):
      with cols[i % 2]:
        if st.checkbox(name, key=f"p4_item_{i}"):
          selected_records_p5.append((col1_val, col2_val, code, name))

    st.markdown("---")
    st.subheader("📋 盤點撥補ZZ產生的清單")
    if selected_records_p5:
      df_p5 = pd.DataFrame(selected_records_p5)
      st.dataframe(df_p5, use_container_width=True, hide_index=True)
      get_excel_download_button(df_p5, "盤點撥補ZZ")
    else:
      st.info("👆 請在上方勾選項目。")
