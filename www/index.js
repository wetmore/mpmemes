// https://stackoverflow.com/a/12475270/1055926
function timeAgo(time) {
  var time_formats = [
    [60, "seconds", 1], // 60
    [120, "1 minute ago", "1 minute from now"], // 60*2
    [3600, "minutes", 60], // 60*60, 60
    [7200, "1 hour ago", "1 hour from now"], // 60*60*2
    [86400, "hours", 3600], // 60*60*24, 60*60
    [172800, "Yesterday", "Tomorrow"], // 60*60*24*2
    [604800, "days", 86400], // 60*60*24*7, 60*60*24
    [1209600, "Last week", "Next week"], // 60*60*24*7*4*2
    [2419200, "weeks", 604800], // 60*60*24*7*4, 60*60*24*7
    [4838400, "Last month", "Next month"], // 60*60*24*7*4*2
    [29030400, "months", 2419200], // 60*60*24*7*4*12, 60*60*24*7*4
    [58060800, "Last year", "Next year"], // 60*60*24*7*4*12*2
    [2903040000, "years", 29030400], // 60*60*24*7*4*12*100, 60*60*24*7*4*12
    [5806080000, "Last century", "Next century"], // 60*60*24*7*4*12*100*2
    [58060800000, "centuries", 2903040000], // 60*60*24*7*4*12*100*20, 60*60*24*7*4*12*100
  ];
  var seconds = (+new Date() - time) / 1000,
    token = "ago",
    list_choice = 1;

  if (seconds == 0) {
    return "Just now";
  }
  if (seconds < 0) {
    seconds = Math.abs(seconds);
    token = "from now";
    list_choice = 2;
  }
  var i = 0,
    format;
  while ((format = time_formats[i++]))
    if (seconds < format[0]) {
      if (typeof format[2] == "string") return format[list_choice];
      else
        return Math.floor(seconds / format[2]) + " " + format[1] + " " + token;
    }
  return time;
}

function sortTable(table, sortInfo) {
  const prevSelectedCol = table.querySelector("thead td.selected");
  if (prevSelectedCol) {
    prevSelectedCol.className = "";
  }
  const selectedCol = table.querySelectorAll("thead td")[sortInfo.ix];
  selectedCol.className = `selected ${sortInfo.dir}`;
  const dimension = selectedCol.textContent;
  console.log(dimension);

  const tbody = table.querySelector("tbody");
  const rows = tbody.querySelectorAll("tr");

  const sorted = [...rows].sort((a, b) => {
    const aCol = a.querySelectorAll("td")[sortInfo.ix];
    const bCol = b.querySelectorAll("td")[sortInfo.ix];

    const aText = aCol.textContent.toLowerCase();
    const bText = bCol.textContent.toLowerCase();

    const aValue = parseFloat(aCol.textContent);
    const bValue = parseFloat(bCol.textContent);

    let comparator;
    if (dimension == "User" || dimension == "Post") {
      if (sortInfo.dir == "asc") {
        comparator = aText < bText ? -1 : aText > bText;
      } else {
        comparator = aText > bText ? -1 : aText < bText;
      }
    } else {
      comparator = sortInfo.dir == "asc" ? aValue - bValue : bValue - aValue;
    }

    return comparator;
  });

  tbody.innerHTML = "";
  for (const [i, row] of sorted.entries()) {
    const rank = sortInfo.dir == "asc" ? sorted.length - i : i + 1;
    row.firstChild.textContent = rank;
    tbody.append(row);
  }
}

function makeSortable(table) {
  // Add line numbers
  const colRow = table.querySelector("thead tr");
  colRow.prepend(document.createElement("td"));

  const bodyRows = table.querySelectorAll("tbody tr");
  for (const [i, row] of bodyRows.entries()) {
    const col = document.createElement("td");
    const rank = document.createTextNode(`${i + 1}`);
    col.append(rank);
    row.prepend(col);
  }

  let sortInfo = null;
  const cols = table.querySelectorAll("thead tr td");
  for (const [i, col] of cols.entries()) {
    // cant sort rank or name
    if (i <= 1) {
      continue;
    }

    col.addEventListener("click", () => {
      if (sortInfo && sortInfo.ix == i && sortInfo.dir == "desc") {
        sortInfo = { ix: i, dir: "asc" };
      } else {
        sortInfo = { ix: i, dir: "desc" };
      }
      sortTable(table, sortInfo);
    });
  }
}

const lastUpdated = document.querySelector("#last-updated");
lastUpdated.textContent = timeAgo(
  1000 * parseFloat(lastUpdated.getAttribute("data-ts"))
);

makeSortable(document.getElementById("users-table"));
makeSortable(document.getElementById("posts-table"));
