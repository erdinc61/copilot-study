import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(
    page_title="Studie zum Thema 'Bewertung der Effizienz des Copilot (ChatGPT) - Einsatzes in der betrieblichen Anwendungsentwicklung durchgeführt' von Erdinc Gürsoy",
    initial_sidebar_state="expanded"
)

FONT = dict(family="Arial", size=12)
CSV_PATH = "Bewertung_der_Effizienz_des_Copilot__ChatGPT___Einsatzes_in_der__betrieblichen_Anwendungsentwicklung.csv"
df_orig = pd.read_csv(CSV_PATH)

st.sidebar.header("Filter")
teil_ids = df_orig["Teilnehmer"].unique().tolist()
teil_sel = st.sidebar.selectbox("Teilnehmer", ["Alle"] + teil_ids)

exp_map = {
    "< 2 Jahre": [c for c in df_orig.columns if "Weniger als 2 Jahre" in c][0],
    "2–5 Jahre": [c for c in df_orig.columns if "2 bis 5 Jahre" in c][0],
    "> 5 Jahre": [c for c in df_orig.columns if "Mehr als 5 Jahre" in c][0],
}
exp_sel = st.sidebar.multiselect("Berufserfahrung (Jahre)", list(exp_map.keys()), default=list(exp_map.keys()))

since_col = [c for c in df_orig.columns if "Seit wann nutzt du GitHub Copilot" in c][0]
since_sel = st.sidebar.multiselect("Länge der Nutzung von Copilot/ChatGPT", sorted(df_orig[since_col].dropna().unique()), default=sorted(df_orig[since_col].dropna().unique()))

freq_col = [c for c in df_orig.columns if "Wie häufig nutzt du GitHub Copilot" in c][0]
freq_sel = st.sidebar.multiselect("Nutzungsfrequenz Copilot/ChatGPT", sorted(df_orig[freq_col].dropna().unique()), default=sorted(df_orig[freq_col].dropna().unique()))

rate_col = [c for c in df_orig.columns if "Wie bewertest du insgesamt" in c][0]
rate_sel = st.sidebar.multiselect("Gesamtbewertung Copilot", sorted(df_orig[rate_col].dropna().unique()), default=sorted(df_orig[rate_col].dropna().unique()))

df = df_orig.copy()
if teil_sel != "Alle":
    df_detail = df[df["Teilnehmer"] == teil_sel]
else:
    mask = pd.Series(False, index=df.index)
    for k in exp_sel:
        mask |= df[exp_map[k]] == 1
    df = df[mask]
    df = df[df[since_col].isin(since_sel)]
    df = df[df[freq_col].isin(freq_sel)]
    df = df[df[rate_col].isin(rate_sel)]
    df_detail = None

if df_detail is None and df.empty:
    st.warning("Keine Daten für diese Filter. Bitte Einstellungen anpassen.")
    st.stop()

if df_detail is not None:
    st.title(f"Antworten Teilnehmer {teil_sel}")
    st.json(df_detail.to_dict(orient="records")[0])
    st.stop()

st.title("Studie zum Thema 'Bewertung der Effizienz des Copilot (ChatGPT) - Einsatzes in der betrieblichen Anwendungsentwicklung' durchgeführt von Erdinc Gürsoy")
st.write(f"{len(df)} Antworten nach Filter")
st.dataframe(df, use_container_width=True)

likert_map = {
    "Stimme gar nicht zu": 1,
    "Stimme eher nicht zu": 2,
    "Weder noch / teils-teils": 3,
    "Stimme eher zu": 4,
    "Stimme voll zu": 5,
}
inv_map = {v: k for k, v in likert_map.items()}

def clean_label(col: str) -> str:
    m = re.search(r"\(([^)]+)\)", col)
    return m.group(1) if m else col

def clean_question(q):
    q = re.sub(r"[\(\[][^)\]]*[\)\]]", "", q)
    q = re.sub(r"Eigene Kriterien|Freitext", "", q, flags=re.IGNORECASE)
    q = re.sub(r"\s+", " ", q)
    q = q.strip(" :-")
    return q

def format_title(frage):
    return '<br>'.join([frage[i:i+70] for i in range(0, len(frage), 70)])

def diagram_with_stats(df_lik, frage, positiv_labels=None, negativ_labels=None, is_likert=True, note_map=None):
    df_lik["Label"] = df_lik["Prozent"] + " (" + df_lik["Absolut"].astype(str) + ")"
    fig = px.bar(
        df_lik, x="Antwort", y="Anteil", 
        text="Label",
        hover_data={"Absolut": True, "Prozent": True}
    )
    fig.update_traces(
        textfont=dict(size=16, color='white', family="Arial"),
        hovertemplate="<br>".join([
            "Absolut=%{customdata[0]}",
            "Prozent=%{customdata[1]}"
        ])
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_tickformat=".0%",
        font=FONT,
        title={"text": format_title(frage), "x":0.5, "xanchor": "center", "y": 0.94, "yanchor": "top"},
        margin={'t': 120}
    )
    st.plotly_chart(fig, use_container_width=True)
    if is_likert and positiv_labels and negativ_labels:
        pos = df_lik[df_lik["Antwort"].isin(positiv_labels)]["Absolut"].sum()
        pos_pct = pos / df_lik["Absolut"].sum()
        neg = df_lik[df_lik["Antwort"].isin(negativ_labels)]["Absolut"].sum()
        neg_pct = neg / df_lik["Absolut"].sum()
        st.markdown(
            f"<b>Positiv (\"Stimme eher zu\" & \"Stimme voll zu\"):</b> {pos} ({pos_pct:.1%}) &nbsp;&nbsp;&nbsp;&nbsp; <b>Negativ (\"Stimme gar nicht zu\" & \"Stimme eher nicht zu\"):</b> {neg} ({neg_pct:.1%})",
            unsafe_allow_html=True,
        )
    if note_map:
        df_lik["NoteNum"] = df_lik["Antwort"].map(note_map)
        schnitt = (df_lik["NoteNum"] * df_lik["Absolut"]).sum() / df_lik["Absolut"].sum()
        st.markdown(f"<b>Notendurchschnitt:</b> {schnitt:.2f}", unsafe_allow_html=True)

positiv_labels = ["Stimme eher zu", "Stimme voll zu"]
negativ_labels = ["Stimme gar nicht zu", "Stimme eher nicht zu"]

if "_Erfahrung" not in df.columns:
    df["_Erfahrung"] = df.apply(lambda r: next(k for k, v in exp_map.items() if r[v] == 1), axis=1)

exp_col = [c for c in df.columns if "Berufserfahrung" in c and "Jahre" in c][0]
frage_exp = clean_question(exp_col)
exp_counts = df["_Erfahrung"].value_counts().reindex(list(exp_map.keys())).fillna(0)
df_exp = pd.DataFrame({
    "Antwort": list(exp_map.keys()),
    "Absolut": exp_counts.values,
    "Anteil": exp_counts.values / len(df)
})
df_exp["Prozent"] = (df_exp["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_exp, frage_exp, is_likert=False)

since_counts = df[since_col].value_counts(normalize=True).sort_index()
abs_since = df[since_col].value_counts().sort_index()
frage_since = clean_question(since_col)
df_since = pd.DataFrame({"Antwort": since_counts.index, "Anteil": since_counts.values, "Absolut": abs_since.values})
df_since["Prozent"] = (df_since["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_since, frage_since, is_likert=False)

freq_counts = df[freq_col].value_counts(normalize=True).sort_index()
abs_freq = df[freq_col].value_counts().sort_index()
frage_freq = clean_question(freq_col)
df_freq = pd.DataFrame({"Antwort": freq_counts.index, "Anteil": freq_counts.values, "Absolut": abs_freq.values})
df_freq["Prozent"] = (df_freq["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_freq, frage_freq, is_likert=False)

rate_counts = df[rate_col].value_counts(normalize=True).sort_index()
abs_rate = df[rate_col].value_counts().sort_index()
frage_rate = clean_question(rate_col)
df_rate = pd.DataFrame({"Antwort": rate_counts.index, "Anteil": rate_counts.values, "Absolut": abs_rate.values})
df_rate["Prozent"] = (df_rate["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_rate, frage_rate, is_likert=False)

task_cols = [c for c in df.columns if c.startswith("Für welche Aufgaben setzt du")]
if task_cols:
    nums = df[task_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum()
    frage_task = clean_question(task_cols[0])
    df_task = pd.DataFrame({"Antwort": [clean_label(c) for c in task_cols], "Absolut": nums.values})
    df_task["Anteil"] = df_task["Absolut"] / len(df)
    df_task["Prozent"] = (df_task["Anteil"] * 100).round(1).astype(str) + "%"
    diagram_with_stats(df_task, frage_task, is_likert=False)

def extract_parenthesis_or_clean(col):
    m = re.search(r"\(([^)]+)\)", col)
    if col.startswith("Wahrnehmung von Copilot im Arbeitsalltag") and m:
        return m.group(1).strip()
    return clean_question(col)

for col in df.columns:
    if col.startswith("Wahrnehmung von Copilot"):
        frage = extract_parenthesis_or_clean(col)
        pct = df[col].map(likert_map).value_counts(normalize=True).sort_index()
        abs_values = df[col].map(likert_map).value_counts().sort_index()
        df_lik = pd.DataFrame({
            "Antwort": [inv_map[i] for i in pct.index],
            "Anteil": pct.values,
            "Absolut": abs_values.values,
        })
        df_lik["Prozent"] = (df_lik["Anteil"] * 100).round(1).astype(str) + "%"
        diagram_with_stats(df_lik, frage, positiv_labels, negativ_labels, is_likert=True)

situ_col = next((c for c in df.columns if "In welchen Situationen" in c and "Freitext" in c), None)
if situ_col:
    st.header("In welchen Situationen ist Copilot besonders hilfreich?")
    situ_frei = df.loc[~df[situ_col].isna(), ["Teilnehmer", situ_col]]
    for i, row in situ_frei.iterrows():
        st.markdown(f'<div title="Teilnehmer: {row.Teilnehmer}">• {row[situ_col]}</div>', unsafe_allow_html=True)

rel_col = [c for c in df.columns if "Wie zuverlässig findest" in c][0]
order_rel = ["ungenügend","mangelhaft","ausreichend","befriedigend","gut","sehr gut"]
note_map = {"ungenügend":6, "mangelhaft":5, "ausreichend":4, "befriedigend":3, "gut":2, "sehr gut":1}
rel_counts = df[rel_col].value_counts(normalize=True).reindex(order_rel).fillna(0)
abs_rel = df[rel_col].value_counts().reindex(order_rel).fillna(0)
frage_rel = clean_question(rel_col)
df_rel = pd.DataFrame({"Antwort": order_rel, "Anteil": rel_counts.values, "Absolut": abs_rel.values})
df_rel["Prozent"] = (df_rel["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_rel, frage_rel, is_likert=False, note_map=note_map)

edit_col = [c for c in df.columns if "Vorschläge nachbearbeiten" in c][0]
edit_counts = df[edit_col].value_counts(normalize=True).sort_index()
abs_edit = df[edit_col].value_counts().sort_index()
frage_edit = clean_question(edit_col)
df_edit = pd.DataFrame({"Antwort": edit_counts.index, "Anteil": edit_counts.values, "Absolut": abs_edit.values})
df_edit["Prozent"] = (df_edit["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_edit, frage_edit, is_likert=False)

err_col = [c for c in df.columns if "fehlerhaften oder riskanten Code" in c][0]
err_counts = df[err_col].value_counts(normalize=True).sort_index()
abs_err = df[err_col].value_counts().sort_index()
frage_err = clean_question(err_col)
df_err = pd.DataFrame({"Antwort": err_counts.index, "Anteil": err_counts.values, "Absolut": abs_err.values})
df_err["Prozent"] = (df_err["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_err, frage_err, is_likert=False)

skip_col = [c for c in df.columns if "Verzichtest du bewusst" in c][0]
skip_counts = df[skip_col].value_counts(normalize=True).sort_index()
abs_skip = df[skip_col].value_counts().sort_index()
frage_skip = clean_question(skip_col)
df_skip = pd.DataFrame({"Antwort": skip_counts.index, "Anteil": skip_counts.values, "Absolut": abs_skip.values})
df_skip["Prozent"] = (df_skip["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_skip, frage_skip, is_likert=False)

cases_col = next((c for c in df.columns if c.strip()=="In welchen Fällen?"), None)
if cases_col:
    st.header("In welchen Fällen?")
    cases_frei = df.loc[~df[cases_col].isna(), ["Teilnehmer", cases_col]]
    for i, row in cases_frei.iterrows():
        st.markdown(f'<div title="Teilnehmer: {row.Teilnehmer}">• {row[cases_col]}</div>', unsafe_allow_html=True)

rec_col = [c for c in df.columns if "professionellen Umfeld empfehlen" in c][0]
rec_counts = df[rec_col].value_counts(normalize=True).sort_index()
abs_rec = df[rec_col].value_counts().sort_index()
frage_rec = clean_question(rec_col)
df_rec = pd.DataFrame({"Antwort": rec_counts.index, "Anteil": rec_counts.values, "Absolut": abs_rec.values})
df_rec["Prozent"] = (df_rec["Anteil"] * 100).round(1).astype(str) + "%"
diagram_with_stats(df_rec, frage_rec, is_likert=False)

limit_col = next((c for c in df.columns if "Wie würdest du den Umgang einschränken" in c), None)
if limit_col:
    st.header("Einschränkung des Einsatzes?")
    limit_frei = df.loc[~df[limit_col].isna(), ["Teilnehmer", limit_col]]
    for i, row in limit_frei.iterrows():
        st.markdown(f'<div title="Teilnehmer: {row.Teilnehmer}">• {row[limit_col]}</div>', unsafe_allow_html=True)

risk_prefix = "Welche der folgenden Aspekte"
risk_cols = [c for c in df.columns if c.startswith(risk_prefix) and re.search(r"\([^)]+\)$", c)]
if risk_cols:
    frage_risk = clean_question([c for c in df.columns if c.startswith(risk_prefix)][0])
    labels = [re.search(r"\(([^)]+)\)$", c).group(1) for c in risk_cols]
    nums = df[risk_cols].apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0).sum()
    perc = nums / len(df)
    df_risk = pd.DataFrame({"Antwort": labels, "Anteil": perc.values, "Absolut": nums.values})
    df_risk["Prozent"] = (df_risk["Anteil"] * 100).round(1).astype(str) + "%"
    diagram_with_stats(df_risk, frage_risk, is_likert=False)

risk_text_col = next((c for c in df.columns if "(Freitext)" in c and risk_prefix in c), None)
if risk_text_col:
    st.subheader("Risiken/Hürden (Freitext)")
    risk_frei = df.loc[~df[risk_text_col].isna(), ["Teilnehmer", risk_text_col]]
    for i, row in risk_frei.iterrows():
        st.markdown(f'<div title="Teilnehmer: {row.Teilnehmer}">• {row[risk_text_col]}</div>', unsafe_allow_html=True)

adv_col = [c for c in df.columns if "Welche Vorteile siehst du persönlich" in c][0]
st.header("Welche Vorteile siehst du persönlich?")
adv_frei = df.loc[~df[adv_col].isna(), ["Teilnehmer", adv_col]]
for i, row in adv_frei.iterrows():
    st.markdown(f'<div title="Teilnehmer: {row.Teilnehmer}">• {row[adv_col]}</div>', unsafe_allow_html=True)

dis_col = [c for c in df.columns if "Welche Nachteile oder Probleme" in c][0]
st.header("Welche Nachteile oder Probleme erlebtest du?")
dis_frei = df.loc[~df[dis_col].isna(), ["Teilnehmer", dis_col]]
for i, row in dis_frei.iterrows():
    st.markdown(f'<div title="Teilnehmer: {row.Teilnehmer}">• {row[dis_col]}</div>', unsafe_allow_html=True)
