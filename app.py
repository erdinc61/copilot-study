import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Studie Copilot/ChatGPT", layout="wide", initial_sidebar_state="expanded")
FONT = dict(family="Arial", size=12)

CSV_PATH = "Bewertung_der_Effizienz_des_Copilot__ChatGPT___Einsatzes_in_der__betrieblichen_Anwendungsentwicklung.csv"
df_orig = pd.read_csv(CSV_PATH)

st.sidebar.header("Filter")
teil_ids = df_orig["Teilnehmer"].unique().tolist()
teil_sel = st.sidebar.selectbox("Teilnehmer anzeigen", ["Alle"] + teil_ids)

exp_map = {
    "< 2 Jahre": [c for c in df_orig.columns if "Weniger als 2 Jahre" in c][0],
    "2–5 Jahre": [c for c in df_orig.columns if "2 bis 5 Jahre" in c][0],
    "> 5 Jahre": [c for c in df_orig.columns if "Mehr als 5 Jahre" in c][0],
}
exp_sel = st.sidebar.multiselect("Berufserfahrung", list(exp_map.keys()), default=list(exp_map.keys()))

since_col = [c for c in df_orig.columns if "Seit wann nutzt du GitHub Copilot" in c][0]
since_sel = st.sidebar.multiselect("Seit wann nutzt du Copilot/ChatGPT?", sorted(df_orig[since_col].dropna().unique()), default=sorted(df_orig[since_col].dropna().unique()))

freq_col = [c for c in df_orig.columns if "Wie häufig nutzt du GitHub Copilot" in c][0]
freq_sel = st.sidebar.multiselect("Wie häufig nutzt du Copilot/ChatGPT?", sorted(df_orig[freq_col].dropna().unique()), default=sorted(df_orig[freq_col].dropna().unique()))

rate_col = [c for c in df_orig.columns if "Wie bewertest du insgesamt" in c][0]
rate_sel = st.sidebar.multiselect("Gesamtbewertung", sorted(df_orig[rate_col].dropna().unique()), default=sorted(df_orig[rate_col].dropna().unique()))

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

st.title("Studie: Bewertung der Effizienz des Copilot (ChatGPT)")
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

st.header("Wie viele Jahre Berufserfahrung besitzt du in der Softwareentwicklung?")
df["_Erfahrung"] = df.apply(lambda r: next(k for k, v in exp_map.items() if r[v] == 1), axis=1)
order_exp = ["< 2 Jahre", "2–5 Jahre", "> 5 Jahre"]
exp_counts = df["_Erfahrung"].value_counts().reindex(order_exp).fillna(0)
df_exp = pd.DataFrame({
    "Erfahrung": order_exp,
    "Absolute": exp_counts.values,
    "Anteil": exp_counts.values / len(df)
})
fig_exp = px.bar(df_exp, x="Erfahrung", y="Anteil", text="Absolute", category_orders={"Erfahrung": order_exp})
fig_exp.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_exp, use_container_width=True)

st.header("Seit wann nutzt du Copilot/ChatGPT?")
since_counts = df[since_col].value_counts(normalize=True).sort_index()
df_since = pd.DataFrame({"Kategorie": since_counts.index, "Anteil": since_counts.values})
fig_since = px.bar(df_since, x="Kategorie", y="Anteil", text=[f"{v:.0%}" for v in df_since["Anteil"]])
fig_since.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_since, use_container_width=True)

st.header("Wie häufig nutzt du Copilot/ChatGPT?")
freq_counts = df[freq_col].value_counts(normalize=True).sort_index()
df_freq = pd.DataFrame({"Häufigkeit": freq_counts.index, "Anteil": freq_counts.values})
fig_freq = px.bar(df_freq, x="Häufigkeit", y="Anteil", text=[f"{v:.0%}" for v in df_freq["Anteil"]])
fig_freq.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_freq, use_container_width=True)

st.header("Wie bewertest du insgesamt den Einsatz von KI-Coding-Assistenten?")
rate_counts = df[rate_col].value_counts(normalize=True).sort_index()
df_rate = pd.DataFrame({"Bewertung": rate_counts.index, "Anteil": rate_counts.values})
fig_rate = px.bar(df_rate, x="Bewertung", y="Anteil", text=[f"{v:.0%}" for v in df_rate["Anteil"]])
fig_rate.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_rate, use_container_width=True)

st.header("Für welche Aufgaben setzt du es hauptsächlich ein?")
task_cols = [c for c in df.columns if c.startswith("Für welche Aufgaben setzt du")]
if task_cols:
    nums = df[task_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum()
    df_task = pd.DataFrame({"Aufgabe": [clean_label(c) for c in task_cols], "Anteil": nums.values / len(df)})
    fig_task = px.bar(df_task, x="Aufgabe", y="Anteil", text=[f"{v:.0%}" for v in df_task["Anteil"]])
    fig_task.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT, xaxis_tickangle=-20)
    st.plotly_chart(fig_task, use_container_width=True)

st.header("Wahrnehmung von Copilot im Arbeitsalltag")
for col in df.columns:
    if col.startswith("Wahrnehmung von Copilot"):
        pct = df[col].map(likert_map).value_counts(normalize=True).sort_index()
        df_lik = pd.DataFrame({"Antwort": [inv_map[i] for i in pct.index], "Anteil": pct.values})
        fig = px.bar(df_lik, x="Antwort", y="Anteil", text=[f"{v:.0%}" for v in df_lik["Anteil"]])
        fig.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
        st.plotly_chart(fig, use_container_width=True)

situ_col = next((c for c in df.columns if "In welchen Situationen" in c and "Freitext" in c), None)
if situ_col:
    st.header("In welchen Situationen ist Copilot besonders hilfreich?")
    for a in df[situ_col].dropna().unique():
        st.write("•", a)

st.header("Wie zuverlässig findest du den vorgeschlagenen Code allgemein?")
rel_col = [c for c in df.columns if "Wie zuverlässig findest" in c][0]
order_rel = ["ungenügend","mangelhaft","ausreichend","befriedigend","gut","sehr gut"]
rel_counts = df[rel_col].value_counts(normalize=True).reindex(order_rel).fillna(0)
df_rel = pd.DataFrame({"Note": order_rel, "Anteil": rel_counts.values})
fig_rel = px.bar(df_rel, x="Note", y="Anteil", text=[f"{v:.0%}" for v in df_rel["Anteil"]])
fig_rel.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_rel, use_container_width=True)

edit_col = [c for c in df.columns if "Vorschläge nachbearbeiten" in c][0]
st.header("Wie oft musst du Vorschläge nachbearbeiten?")
edit_counts = df[edit_col].value_counts(normalize=True).sort_index()
df_edit = pd.DataFrame({"Häufigkeit": edit_counts.index, "Anteil": edit_counts.values})
fig_edit = px.bar(df_edit, x="Häufigkeit", y="Anteil", text=[f"{v:.0%}" for v in df_edit["Anteil"]])
fig_edit.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_edit, use_container_width=True)

err_col = [c for c in df.columns if "fehlerhaften oder riskanten Code" in c][0]
st.header("Gab es fehlerhaften oder riskanten Code durch Copilot?")
err_counts = df[err_col].value_counts(normalize=True).sort_index()
df_err = pd.DataFrame({"Antwort": err_counts.index, "Anteil": err_counts.values})
fig_err = px.bar(df_err, x="Antwort", y="Anteil", text=[f"{v:.0%}" for v in df_err["Anteil"]])
fig_err.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_err, use_container_width=True)

skip_col = [c for c in df.columns if "Verzichtest du bewusst" in c][0]
st.header("Verzicht auf Copilot?")
skip_counts = df[skip_col].value_counts(normalize=True).sort_index()
df_skip = pd.DataFrame({"Antwort": skip_counts.index, "Anteil": skip_counts.values})
fig_skip = px.bar(df_skip, x="Antwort", y="Anteil", text=[f"{v:.0%}" for v in df_skip["Anteil"]])
fig_skip.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_skip, use_container_width=True)

cases_col = next((c for c in df.columns if c.strip()=="In welchen Fällen?"), None)
if cases_col:
    st.header("In welchen Fällen?")
    for a in df[cases_col].dropna().unique():
        st.write("•", a)

rec_col = [c for c in df.columns if "professionellen Umfeld empfehlen" in c][0]
st.header("Empfehlung im professionellen Umfeld?")
rec_counts = df[rec_col].value_counts(normalize=True).sort_index()
df_rec = pd.DataFrame({"Antwort": rec_counts.index, "Anteil": rec_counts.values})
fig_rec = px.bar(df_rec, x="Antwort", y="Anteil", text=[f"{v:.0%}" for v in df_rec["Anteil"]])
fig_rec.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT)
st.plotly_chart(fig_rec, use_container_width=True)

limit_col = next((c for c in df.columns if "Wie würdest du den Umgang einschränken" in c), None)
if limit_col:
    st.header("Einschränkung des Einsatzes?")
    for a in df[limit_col].dropna().unique():
        st.write("•", a)

risk_prefix = "Welche der folgenden Aspekte"
risk_cols = [c for c in df.columns if c.startswith(risk_prefix) and re.search(r"\([^)]+\)$", c)]
if risk_cols:
    st.header("Risiken oder Hürden?")
    nums = df[risk_cols].apply(lambda col: pd.to_numeric(col, errors="coerce")).fillna(0).sum()
    perc = nums / len(df)
    labels = [re.search(r"\(([^)]+)\)$", c).group(1) for c in risk_cols]
    df_risk = pd.DataFrame({"Aspekt": labels, "Anteil": perc.values})
    fig_risk = px.bar(df_risk, x="Aspekt", y="Anteil", text=[f"{v:.0%}" for v in df_risk["Anteil"]])
    fig_risk.update_layout(xaxis_title="", yaxis_tickformat=".0%", font=FONT, xaxis_tickangle=-20)
    st.plotly_chart(fig_risk, use_container_width=True)

risk_text_col = next((c for c in df.columns if "(Freitext)" in c and risk_prefix in c), None)
if risk_text_col:
    st.subheader("Risiken/Hürden (Freitext)")
    for a in df[risk_text_col].dropna().unique():
        st.write("•", a)

adv_col = [c for c in df.columns if "Welche Vorteile siehst du persönlich" in c][0]
st.header("Welche Vorteile siehst du persönlich?")
for a in df[adv_col].dropna().unique():
    st.write("•", a)

dis_col = [c for c in df.columns if "Welche Nachteile oder Probleme" in c][0]
st.header("Welche Nachteile oder Probleme erlebtest du?")
for a in df[dis_col].dropna().unique():
    st.write("•", a)
