<html lang="fr">
<head>
<meta charset="utf-8">
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:20px}
  table{border-collapse:collapse;width:100%;max-width:400px}
  th,td{border:1px solid #dd;padding:8px;text-align:right}
  th{background:#f3f3f3;text-align:left}
  caption{font-weight:600;margin-bottom:8px;text-align:left}
</style>
</head>
<body>
<table id="tbl"><caption>Observations</caption>
<thead><tr><th>Date (UTC)</th><th>Débit (l/s)</th></tr></thead>
<tbody></tbody>
</table>
<script>
const url = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite=H774201001&size=5&pretty&grandeur_hydro=Q&fields=date_obs,resultat_obs,continuite_obs_hydro";
fetch(url)
  .then(r=>r.json())
  .then(j=>{
    const tbody = document.querySelector("#tbl tbody");
    j.data.forEach(it=>{
      const tr=document.createElement("tr");
      const d=new Date(it.date_obs).toISOString().replace("T"," ").replace("Z","");
      tr.innerHTML=`<td style="text-align:left">${d}</td><td>${it.resultat_obs ?? "—"}</td><td style="text-align:center"></td>`;
      tbody.appendChild(tr);
    });
  })
  .catch(e=>{ document.querySelector("tbody").innerHTML=`<tr><td colspan="2">Erreur: ${e.message}</td></tr>` });
</script>
</body>
</html>
