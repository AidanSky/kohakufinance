// labels for x and y ? 
const ctx = document.getElementById('stockChart').getContext('2d');
const stockChart = new Chart(ctx, {
    type: 'line', // Or another type based on selection? 
    data: {
        labels: [], // Initialize with empty data
        datasets: [],
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Date',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Price',
                },
            },
        },
        elements: {
            point: {
                radius: 0,
            },
        }
    },
});

const rsiChart = new Chart(document.getElementById('rsiChart').getContext('2d'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [],
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false,
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Date',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'RSI',
                },
                min: 0,
                max: 100,
                ticks: {
                    stepSize: 20,
                },
            },
        },
        elements: {
            point: {
                radius: 0,
            },
        }
    },
});

function errorFunction(message) {
    console.error("Error Function", message);
    const errorMessage = document.getElementById('errorMessage');
    const errorDiv = document.getElementById('errorDiv');

    errorMessage.textContent = message;
    errorDiv.classList.remove('d-none');
}

document.getElementById('clearError').addEventListener('click', () => {
    document.getElementById('errorDiv').classList.add('d-none');
});

// Event listener for RSI button to display RSI chart
const rsiSelection = document.getElementById('rsiSelection')
const rsiSelectionLabel = document.getElementById('rsiSelectionLabel')
const smaSelectionLabel = document.getElementById('smaSelectionLabel')
const smaSelection = document.getElementById('smaSelection')

document.getElementById('rsiButton').addEventListener('change', function() {
    const rsiChart = document.getElementById('rsiChart');
    if (this.checked) {
        rsiChart.classList.remove('d-none');
        rsiSelection.classList.remove('d-none')
        rsiSelectionLabel.classList.remove('d-none')
        
    } else {
        rsiChart.classList.add('d-none');
        rsiSelection.classList.add('d-none')
        rsiSelectionLabel.classList.add('d-none')
    }
});

document.getElementById('smaButton').addEventListener('change', function() {
    const rsiChart = document.getElementById('rsiChart');
    if (this.checked) {
        smaSelection.classList.remove('d-none')
        smaSelectionLabel.classList.remove('d-none')
        
    } else {
        smaSelection.classList.add('d-none')
        smaSelectionLabel.classList.add('d-none')
    }
});



// Event listener to hide/show SMA and RSI buttons
document.getElementById('selectedFunction').addEventListener('change', function() {
    if (this.value === 'graph') {
        document.getElementById('technicalAnalysis').classList.remove('d-none');
    }
    else {
        document.getElementById('technicalAnalysis').classList.add('d-none');
    }
});
// Create Event Listener To Update Chart                     
const updateChartButton = document.getElementById('updateChart') 
updateChartButton.addEventListener('click', async () => { // double check**
    const selectedFunction = document.getElementById('selectedFunction').value;
    const symbol = document.getElementById('stockSymbol').value;
    const datatype = document.getElementById('dataType').value;
    const startdate = document.getElementById('startDate').value;
    const enddate = document.getElementById('endDate').value;

    // Only necessary if 2nd symbol is selected for comparison function
    const secondSymbolValue = document.getElementById('secondSymbol').value;

    // Used if SMA or RSI are plotted
    const rsiLength = document.getElementById('rsiSelection').value;
    const smaLength = document.getElementById('smaSelection').value;

    // return check for if RSI or SMA buttons are selected
    const rsiButton = document.getElementById('rsiButton');
    const smaButton = document.getElementById('smaButton');

    // return check for if custom date range is selected
    const customRange = document.getElementById('customRange');

    // Check date range if it is needed
    const dateRange = document.querySelector('input[name="dateRange"]:checked').value;

    // return data to python based on what was selected via fetch

    const requestData = {
        function: selectedFunction,
        ticker: symbol,
        dataType: datatype,
        startDate: startdate,
        endDate: enddate,
        secondSymbol: secondSymbolValue,
        rsiLength: rsiLength,
        smaLength: smaLength,
        rsiButton: rsiButton.checked,
        smaButton: smaButton.checked,
        customRange: customRange.checked,
        dateRange: dateRange,
    };

    // debugging 
    console.log("requestData:", requestData)

    try {
        const response = await fetch("/fetch-data", {
            method: "POST", 
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(requestData),
        });

        const responseData = await response.json();

        // debugging 
        console.log("responseData:", responseData);
        console.log("requestData", requestData);

        console.log("symbol", symbol)
        console.log("secondsymbol", secondSymbolValue)
        console.log("selected Function", selectedFunction)

        if (!response.ok) {
            throw new Error(responseData.error);
        }
        else if ((responseData.startDate === null || responseData.endDate === null) && customRange.checked) {
            throw new Error("Invalid Date Range");
        }
        else {
            if (!document.getElementById('errorDiv').classList.contains('d-none'))
                document.getElementById('errorDiv').classList.add('d-none')
        }

        stockChart.data.labels = responseData.labels;
        // update data for chart via if statements for each function 
        if (selectedFunction === "compare") {
            stockChart.data.datasets = [
                {
                    label: symbol.toUpperCase(),
                    data: responseData.dataalpha,
                    borderWidth: 3,
                },
                {
                    label: secondSymbolValue.toUpperCase(),
                    data: responseData.databeta,
                    borderWidth: 3,
                },
            ];
        } else if (selectedFunction ==="percentage") {
            stockChart.data.datasets = [
                {
                    label: symbol.toUpperCase(),
                    data: responseData.data,
                    borderWidth: 3,
                },
            ];
        } else if (selectedFunction === "graph" || selectedFunction === "movingavg") {
            console.log("Test", responseData)
            stockChart.data.datasets = [
                {
                    label: symbol.toUpperCase(),
                    data: responseData.data,
                    borderWidth: 3,
                    fill: false,
                },
            ];
        } if (rsiButton.checked && selectedFunction === "graph") {
                rsiChart.data.labels = responseData.labels;
                console.log("RSI Data:", responseData.rsi);
                rsiChart.data.datasets = [
                    {
                        label: "RSI",
                        data: responseData.rsi,
                        borderColor: 'red',
                        borderWidth: 3,
                        fill: false,
                    },
                    {
                        data: responseData.overbought,
                        borderWidth: 3,
                        borderColor: "black",
                        fill: false,
                    },
                    {
                        data: responseData.oversold,
                        borderWidth: 3,
                        borderColor: "black",
                        fill: false,
                    },
                ];
            } if (smaButton.checked && selectedFunction === "graph") {
                stockChart.data.datasets.push({
                    label: `SMA ${smaLength}`,
                    data: responseData.sma,
                    borderWidth: 3,
                    fill: false,
                });
            }  
        stockChart.update();
        if (rsiButton.checked && selectedFunction === "graph") {
            rsiChart.update();
        }
    } catch (error) {
        errorFunction(error.message);
        console.error("Error test", error.message);
    }
});

// Update available options for chart data if unique, such as SMA, RSI, Compare, etc 
function updateOptions(selectedFunction) {
    const dataType = document.getElementById('dataType');
    const secondSymbolLabel = document.getElementById('secondSymbolLabel')
    const secondSymbol = document.getElementById('secondSymbol')
    const numberSelect = document.getElementById('numberSelect') 
    // dataType.innerHTML = '';
    if (selectedFunction === 'graph') {
        secondSymbol.classList.add('d-none');
        secondSymbolLabel.classList.add('d-none');
    } else if (selectedFunction === 'movingavg') {
        smaSelection.classList.remove('d-none');
        smaSelectionLabel.classList.remove('d-none')
        rsiSelection.classList.add('d-none');
        rsiSelectionLabel.classList.add('d-none');
        rsiChart.canvas.classList.add('d-none');
        rsiButton.checked = false;
        smaButton.checked = false;
        secondTicker.style.display = 'none';
    } else if (selectedFunction === "compare") {
        secondSymbol.classList.remove('d-none');
        secondSymbolLabel.classList.remove('d-none');
        smaSelectionLabel.classList.add('d-none');
        smaSelection.classList.add('d-none');
        rsiSelection.classList.add('d-none');
        rsiSelectionLabel.classList.add('d-none');
        rsiChart.canvas.classList.add('d-none');
        rsiButton.checked = false;
        smaButton.checked = false;
    } else {
        secondSymbol.classList.add('d-none');
        secondSymbolLabel.classList.add('d-none');
        smaSelectionLabel.classList.add('d-none');
        smaSelection.classList.add('d-none');
        rsiSelection.classList.add('d-none');
        rsiSelectionLabel.classList.add('d-none');
        rsiChart.canvas.classList.add('d-none');
        rsiButton.checked = false;
        smaButton.checked = false;
    }
}
// Event listener for the top-level selector
const functionSelector = document.getElementById('selectedFunction');
functionSelector.addEventListener('change', () => {
    const selectedFunction = functionSelector.value;
    updateOptions(selectedFunction);
});

// Event listener for the RSI button
const rsiButton = document.getElementById('rsiButton');
rsiButton.addEventListener('change', () => {
    const selectedFunction = functionSelector.value;
    updateOptions(selectedFunction);
});

// Event listener for the SMA button
const smaButton = document.getElementById('smaButton');
smaButton.addEventListener('change', () => {
    const selectedFunction = functionSelector.value;
    updateOptions(selectedFunction);
});

// Event Listener for Data Range toggler (which should show which should hide)
const customRange = document.getElementById('customRange');
const premadelabel = document.getElementsByClassName('premadelabel');
const startDate = document.getElementById('startDate');
const endDate = document.getElementById('endDate');
customRange.addEventListener('change', function () {
    if (this.checked) {
        for (let i = 0; i < premadelabel.length; i++) {
            startDate.classList.remove('d-none');
            endDate.classList.remove('d-none');
            premadelabel[i].classList.add('d-none');
        }
    } else {
        for (let i = 0; i < premadelabel.length; i++) {
            startDate.classList.add('d-none');
            endDate.classList.add('d-none');
            premadelabel[i].classList.remove('d-none');
        }
    }
});

//Block days after today for calendar element
const today = new Date().toISOString().slice(0, 10);
document.getElementById('endDate').setAttribute("max", today);
document.getElementById('startDate').setAttribute("max", today);