(function () {
    let template = document.createElement("template");
    template.innerHTML = `
    <style>
        :host {}

        div {
            margin: 10px auto;
            max-width: 600px;
        }
        .header-container {
            display: flex;
            align-items: left;
            justify-content: left;
        }

        .input-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .input-container input[type="date"] {
            width: 150px; 
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 50px;
        }

        .input-container label {
            font-size: 16px;
        }

        /* Reset Button Alignment */
        .reset-button-container {
            display: flex;
            justify-content: flex-end;
        }

        input {
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 50px;
            width: 70%;
        }

        button {
            padding: 10px;
            font-size: 16px;
            background-color: #3cb6a9;
            color: #fff;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            width: 20%;
        }

        textarea {
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 96%;
        }
    </style>

    <div class="header-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/ChatGPT-Logo.png/1200px-ChatGPT-Logo.png" width="150"/>
        <h1>ChatGPT</h1>
        <div class="input-container" id="commodity-container">
            <select id="commodity-input">
                <option value="globalsugar">Global Sugar</option>
                <option value="europeansugar">European Sugar</option>
            </select>
        </div>
    </div>

    <div class="input-container" id="analysis-container">
        <label for="start-date">Start</label> <!-- Label for start date -->
        <input type="date" id="start-date" placeholder="Start Date">
        <label for="end-date">End</label> <!-- Label for end date -->
        <input type="date" id="end-date" placeholder="End Date">
        <button id="analysis-button">Analysis</button>
    </div>

    <div class="input-container" id="forecast-container">
        <label for="forecast-date">Forecast End</label> <!-- Label for forecast end date -->
        <input type="date" id="forecast-date" placeholder="Forecast End Date">
        <button id="forecast-button">Forecast</button>
    </div>

    <textarea id="generated-text" rows="10" cols="50" readonly></textarea>
    <div class="reset-button-container">
        <button id="reset-button">Reset</button>
    </div>
    </div>
    `;

    class Widget extends HTMLElement {
        constructor() {
            super();
            let shadowRoot = this.attachShadow({mode: "open"});
            shadowRoot.appendChild(template.content.cloneNode(true));
            this._props = {};
        }

        async connectedCallback() {
            this.init();
        }

        async init() {
            const analysisButton = this.shadowRoot.getElementById("analysis-button");
            analysisButton.addEventListener("click", async () => {
                const startDate = this.convertDate(this.shadowRoot.getElementById("start-date").value);
                const endDate = this.convertDate(this.shadowRoot.getElementById("end-date").value);
                const commodity = this.shadowRoot.getElementById("commodity-input").value;
                const generatedText = this.shadowRoot.getElementById("generated-text");
                generatedText.value = "Analysis in progress...";
                // Implement the analysis logic and fetch call here
                try {
                    const response = await fetch("https://finaigpt-public.eu.ngrok.io/generate_response", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            // Add any additional headers your backend requires
                        },
                        body: JSON.stringify({
                            start_date: startDate,
                            end_date: endDate,
                            commodity: commodity,
                            prompt_type: "analysis"
                        })
                    });

                    if (response.status === 200) {
                        const data = await response.json();
                        generatedText.value = data.generatedText; // Assuming 'generatedText' is a key in your response JSON
                    } else {
                        generatedText.value = "Error: Unable to generate text: " + response.status;
                    }
                } catch (error) {
                    console.error("Fetch error:", error);
                    generatedText.value = "Network error: " + error.message;
                }
            });

            const forecastButton = this.shadowRoot.getElementById("forecast-button");
            forecastButton.addEventListener("click", async () => {
                //const startDate = this.convertDate()
                const endDate = this.convertDate(this.shadowRoot.getElementById("forecast-date").value);
                const commodity = this.shadowRoot.getElementById("commodity-input").value;
                const generatedText = this.shadowRoot.getElementById("generated-text");
                generatedText.value = "Forecast in progress...";
                // Implement the forecast logic and fetch call here
                try {
                    const response = await fetch("https://finaigpt-public.eu.ngrok.io/generate_response", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            // Add any additional headers your backend requires
                        },
                        body: JSON.stringify({
                            start_date: "31/12/2023", //Aktueller Stand der Database
                            end_date: endDate,
                            commodity: commodity,
                            prompt_type: "forecast"
                        })
                    });

                    if (response.status === 200) {
                        const data = await response.json();
                        generatedText.value = data.generatedText; // Assuming 'generatedText' is a key in your response JSON
                    } else {
                        generatedText.value = "Error: Unable to generate text: " + response.status;
                    }
                } catch (error) {
                    console.error("Fetch error:", error);
                    generatedText.value = "Network error: " + error.message;
                }
            });
            const resetButton = this.shadowRoot.getElementById("reset-button");
            resetButton.addEventListener("click", () => {
                const generatedText = this.shadowRoot.getElementById("generated-text");
                generatedText.value = "";
            });
        }

        convertDate(inputFormat) {
            return inputFormat.replace(/\./g, '/');
        }

        onCustomWidgetBeforeUpdate(changedProperties) {
            this._props = {
                ...this._props,
                ...changedProperties
            };
        }

        onCustomWidgetAfterUpdate(changedProperties) {
            this.initMain();
        }
    }

    customElements.define("finai-chatgpt-widget", Widget);
})();
