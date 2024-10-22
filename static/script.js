document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('dateSearchButton').addEventListener('click', function() {
        var startDate = document.getElementById('startDate').value;
        var endDate = document.getElementById('endDate').value;
        
        fetch(`/contrevenants?du=${startDate}&au=${endDate}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error in response');
                }
                return response.json();
            })
            .then(data => {
                console.log("Données reçues:", data);
                const table = document.getElementById('resultsTableDate');
                const tbody = table.getElementsByTagName('tbody')[0];
                tbody.innerHTML = '';
    
                if (data.length === 0) {
                    const row = tbody.insertRow();
                    const cell = row.insertCell(0);
                    cell.textContent = "Aucune donnée trouvée.";
                    cell.colSpan = 2; 
                    table.style.display = 'table';
                } else {
                    data.forEach(violation => {
                        const row = tbody.insertRow();
                        const cell1 = row.insertCell(0);
                        const cell2 = row.insertCell(1);
                        cell1.textContent = violation.etablissement;
                        cell2.textContent = violation.nombre_contraventions;
                    });
                    table.style.display = 'table';
                }
            })
            .catch(error => console.error('Erreur fetch:', error));
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('establishmentSearchButton').addEventListener('click', function() {
        var establishmentName = document.getElementById('establishmentSelect').value;
        fetch(`/violations_by_name?name=${encodeURIComponent(establishmentName)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error in response');
                }
                return response.json();
            })
            .then(data => {
                console.log("Données reçues:", data);
                const table = document.getElementById('resultsTableName');
                const tbody = table.getElementsByTagName('tbody')[0];
                tbody.innerHTML = '';
    
                if (data.length === 0) {
                    const row = tbody.insertRow();
                    const cell = row.insertCell(0);
                    cell.textContent = "Aucune donnée trouvée.";
                    cell.colSpan = 2; 
                    table.style.display = 'table';
                } else {
                    data.forEach(violation => {
                        const row = tbody.insertRow();
                        const cellEtablis = row.insertCell(0);
                        const cellDesc = row.insertCell(1);
                        cellEtablis.textContent = violation.etablissement;
                        cellDesc.textContent = violation.description;
                    });
                    table.style.display = 'table'; 
                }
            })
            .catch(error => console.error('Erreur:', error));
    });    
});
let isEstablishmentsLoaded = false;

document.getElementById('toggleEstablishmentsButton').addEventListener('click', function() {
    const table = document.getElementById('establishmentsViolationsTable');
    const button = document.getElementById('toggleEstablishmentsButton');
    
    if (table.style.display === "none" || table.style.display === "") {
        table.style.display = "table"; 
        button.textContent = "Cacher les établissements";
        
        if (!isEstablishmentsLoaded) {
            fetch('/establishments/violations')
                .then(response => response.json())
                .then(data => {
                    const tableBody = table.querySelector('tbody');
                    tableBody.innerHTML = ""; 
                    data.forEach(establishment => {
                        const row = document.createElement('tr');
                        row.innerHTML = `<td>${establishment.etablissement}</td><td>${establishment.nombre_contraventions}</td>`;
                        tableBody.appendChild(row);
                    });
                    isEstablishmentsLoaded = true; 
                })
                .catch(error => console.error('Error fetching data:', error));
        }
    } else {
        table.style.display = "none"; 
        button.textContent = "Afficher les établissements";
    }
});

let xmlEstablishmentsLoaded = false;

document.getElementById('toggleXMLButton').addEventListener('click', function() {
    const table = document.getElementById('establishmentsViolationsTable');
    const button = document.getElementById('toggleXMLButton');
    
    if (table.style.display === "none" || table.style.display === "") {
        table.style.display = "table"; 
        button.textContent = "Cacher les établissements (XML)";
        
        if (!xmlEstablishmentsLoaded) {
            fetch('/establishments/violations/xml')
                .then(response => response.text()) 
                .then(str => {
                    const parser = new DOMParser();
                    const xmlDoc = parser.parseFromString(str, "text/xml");
                    const establishments = xmlDoc.getElementsByTagName("establishment");

                    const tableBody = table.querySelector('tbody');
                    tableBody.innerHTML = ""; 

                    Array.from(establishments).forEach(est => {
                        const name = est.getElementsByTagName("name")[0].childNodes[0].nodeValue;
                        const count = est.getElementsByTagName("violationsCount")[0].childNodes[0].nodeValue;
                        
                        const row = document.createElement('tr');
                        row.innerHTML = `<td>${name}</td><td>${count}</td>`;
                        tableBody.appendChild(row);
                    });

                    xmlEstablishmentsLoaded = true; 
                })
                .catch(error => console.error('Error fetching XML data:', error));
        }
    } else {
        table.style.display = "none"; 
        button.textContent = "Afficher les établissements (XML)";
    }
});

let csvEstablishmentsLoaded = false;

document.getElementById('fetchCSVEstablishmentsButton').addEventListener('click', function() {
    const table = document.getElementById('establishmentsViolationsTable');
    const button = document.getElementById('fetchCSVEstablishmentsButton');

    if (table.style.display === "none" || table.style.display === "") {
        table.style.display = "table"; 
        button.textContent = "Cacher les établissements (CSV)";

        if (!csvEstablishmentsLoaded) {
            fetch('/establishments/violations/csv')
                .then(response => response.text()) 
                .then(csvText => {
                    const rows = csvText.split('\n').map(row => row.split(','));
                    const headers = rows.shift(); 

                    const tableBody = table.querySelector('tbody');
                    tableBody.innerHTML = ""; 
                    
                    rows.forEach((row, rowIndex) => {
                        if (row.length === headers.length) {
                            const rowElement = document.createElement('tr');
                            row.forEach((cell, cellIndex) => {
                                const cellElement = document.createElement('td');
                                cellElement.textContent = cell;
                                rowElement.appendChild(cellElement);
                            });
                            tableBody.appendChild(rowElement);
                        }
                    });

                    csvEstablishmentsLoaded = true; 
                })
                .catch(error => console.error('Error fetching CSV data:', error));
        }
    } else {
        table.style.display = "none"; 
        button.textContent = "Afficher les établissements (CSV)";
    }
});
