// ============================================================
// RAPTOR DASHBOARD
// Replay + Rolling Five-Step Forecast
// ============================================================

let replayData = [];
let currentIndex = 0;

let replayTimer = null;
let replaySpeed = 1;

// Forecast request state
let forecastInFlight = false;
let pendingForecastIndex = null;

// Tuned alert threshold
const RAPTOR_THRESHOLD = 0.05;


// ============================================================
// LOAD REPLAY DATA
// ============================================================

async function loadReplay() {

    console.log("RAPTOR: Loading replay data...");

    try {

        const response = await fetch("/api/replay");

        if (!response.ok) {
            throw new Error(
                `Replay API returned ${response.status}`
            );
        }

        const data = await response.json();

        replayData = data.predictions || [];

        console.log(
            "RAPTOR: Replay states loaded:",
            replayData.length
        );


        if (replayData.length === 0) {

            console.warn(
                "RAPTOR: No replay data available."
            );

            return;
        }


        // Setup slider
        setupTimeline();


        // Start from first state
        currentIndex = 0;


        // Display first state
        updateDashboard(
            replayData[currentIndex]
        );


    } catch (error) {

        console.error(
            "RAPTOR replay error:",
            error
        );

        const position =
            document.getElementById(
                "replay-position"
            );

        if (position) {
            position.textContent =
                "Replay unavailable";
        }
    }
}


// ============================================================
// UPDATE CURRENT DASHBOARD
// ============================================================

function updateDashboard(prediction) {

    if (!prediction) {
        return;
    }


    // --------------------------------------------------------
    // Attack probability
    // --------------------------------------------------------

    const attackProbability =
        Number(
            prediction.attack_probability || 0
        );


    // --------------------------------------------------------
    // Attack ratio
    // --------------------------------------------------------

    const attackRatio =
        Number(
            prediction.attack_ratio || 0
        );


    // --------------------------------------------------------
    // Stage confidence
    // --------------------------------------------------------

    const confidence =
        Number(
            prediction.stage_confidence || 0
        );


    // --------------------------------------------------------
    // Attack probability card
    // --------------------------------------------------------

    const probabilityElement =
        document.getElementById(
            "attack-probability"
        );


    if (probabilityElement) {

        probabilityElement.textContent =
            (attackProbability * 100).toFixed(2) + "%";
    }


    // --------------------------------------------------------
    // Attack ratio card
    // --------------------------------------------------------

    const ratioElement =
        document.getElementById(
            "attack-ratio"
        );


    if (ratioElement) {

        ratioElement.textContent =
            (attackRatio * 100).toFixed(2) + "%";
    }


    // --------------------------------------------------------
    // Attack stage card
    // --------------------------------------------------------

    const stageElement =
        document.getElementById(
            "attack-stage"
        );


    if (stageElement) {

        stageElement.textContent =
            prediction.attack_stage || "Unknown";
    }


    // --------------------------------------------------------
    // Stage confidence card
    // --------------------------------------------------------

    const confidenceElement =
        document.getElementById(
            "stage-confidence"
        );


    if (confidenceElement) {

        confidenceElement.textContent =
            (confidence * 100).toFixed(2) + "%";
    }


    // --------------------------------------------------------
    // Network time
    // --------------------------------------------------------

    const forecastTimeElement =
        document.getElementById(
            "forecast-time"
        );


    if (forecastTimeElement) {

        forecastTimeElement.textContent =
            formatTime(
                prediction.time_window
            );
    }


    // --------------------------------------------------------
    // Threat status
    // --------------------------------------------------------

    updateThreatStatus(
        attackProbability
    );


    // --------------------------------------------------------
    // Replay position
    // --------------------------------------------------------

    updateReplayPosition();


    // --------------------------------------------------------
    // Five-step forecast
    // --------------------------------------------------------

    loadForecast(currentIndex);
}


// ============================================================
// THREAT STATUS
// ============================================================

function updateThreatStatus(probability) {

    const status =
        document.getElementById(
            "threat-status"
        );


    if (!status) {
        return;
    }


    if (probability >= 0.70) {

        status.textContent =
            "HIGH RISK";

        status.style.color =
            "#ff6b6b";

    }

    else if (probability >= 0.30) {

        status.textContent =
            "ELEVATED";

        status.style.color =
            "#e8c66d";

    }

    else if (probability >= RAPTOR_THRESHOLD) {

        status.textContent =
            "EARLY WARNING";

        status.style.color =
            "#e8c66d";

    }

    else {

        status.textContent =
            "LOW RISK";

        status.style.color =
            "#70d99a";
    }
}


// ============================================================
// LOAD FIVE-STEP FORECAST
// ============================================================

async function loadForecast(index) {

    if (
        replayData.length === 0 ||
        index < 0
    ) {
        return;
    }


    // Always keep the newest requested index
    pendingForecastIndex = index;


    /*
     * If another forecast is already running,
     * don't start another request.
     *
     * The newest index will be processed after
     * the current request finishes.
     */

    if (forecastInFlight) {
        return;
    }


    forecastInFlight = true;


    while (
        pendingForecastIndex !== null
    ) {

        const forecastIndex =
            pendingForecastIndex;


        pendingForecastIndex = null;


        console.log(
            "RAPTOR: Requesting forecast:",
            forecastIndex
        );


        try {

            const response =
                await fetch(
                    `/api/forecast/${forecastIndex}`
                );


            if (!response.ok) {

                throw new Error(
                    `Forecast API returned ${response.status}`
                );
            }


            const data =
                await response.json();


            /*
             * Only render a forecast if it is still
             * relevant enough.
             *
             * If replay has moved several states ahead,
             * the loop below will immediately request
             * the newest position.
             */

            renderForecast(
                data.forecast || []
            );


            console.log(
                "RAPTOR: Forecast rendered:",
                forecastIndex
            );


        } catch (error) {

            console.error(
                "RAPTOR forecast error:",
                error
            );


            const container =
                document.getElementById(
                    "forecast-container"
                );


            if (container) {

                container.innerHTML = `
                    <div class="forecast-error">
                        Unable to load forecast
                    </div>
                `;
            }
        }


        /*
         * If replay moved while the request was
         * executing, pendingForecastIndex now contains
         * the latest replay position.
         *
         * The while loop will process it.
         */
    }


    forecastInFlight = false;
}


// ============================================================
// RENDER FIVE-STEP FORECAST
// ============================================================

function renderForecast(forecast) {

    const container =
        document.getElementById(
            "forecast-container"
        );


    if (!container) {

        console.error(
            "RAPTOR: forecast-container not found."
        );

        return;
    }


    if (
        !forecast ||
        forecast.length === 0
    ) {

        container.innerHTML = `
            <div class="forecast-error">
                No forecast available
            </div>
        `;

        return;
    }


    container.innerHTML =
        forecast
            .map(item => {

                const probability =
                    Number(
                        item.attack_probability || 0
                    ) * 100;


                const ratio =
                    Number(
                        item.attack_ratio || 0
                    ) * 100;


                const confidence =
                    Number(
                        item.stage_confidence || 0
                    ) * 100;


                const stage =
                    item.attack_stage ||
                    "Unknown";


                const step =
                    item.step ||
                    0;


                return `

                    <div class="forecast-card">

                        <div class="forecast-step">
                            T+${step}
                        </div>


                        <div class="forecast-time">
                            ${formatTime(item.time_window)}
                        </div>


                        <div class="forecast-row">

                            <span>
                                ATTACK PROBABILITY
                            </span>

                            <strong>
                                ${probability.toFixed(2)}%
                            </strong>

                        </div>


                        <div class="forecast-row">

                            <span>
                                STAGE
                            </span>

                            <strong>
                                ${stage}
                            </strong>

                        </div>


                        <div class="forecast-row">

                            <span>
                                ATTACK RATIO
                            </span>

                            <strong>
                                ${ratio.toFixed(2)}%
                            </strong>

                        </div>


                        <div class="forecast-row">

                            <span>
                                CONFIDENCE
                            </span>

                            <strong>
                                ${confidence.toFixed(2)}%
                            </strong>

                        </div>

                    </div>

                `;

            })
            .join("");
}


// ============================================================
// START REPLAY
// ============================================================

function startReplay() {

    stopReplay();


    if (replayData.length === 0) {

        console.warn(
            "RAPTOR: Cannot start replay. No data."
        );

        return;
    }


    replayTimer =
        setInterval(() => {


            // End of replay

            if (
                currentIndex >=
                replayData.length - 1
            ) {

                stopReplay();

                setPlayButton(
                    "▶ PLAY"
                );

                return;
            }


            // Move one temporal state forward

            currentIndex++;


            console.log(
                "RAPTOR replay:",
                currentIndex,
                replayData[
                    currentIndex
                ]?.time_window
            );


            // Update dashboard immediately

            updateDashboard(
                replayData[
                    currentIndex
                ]
            );


        }, 1000 / replaySpeed);
}


// ============================================================
// STOP REPLAY
// ============================================================

function stopReplay() {

    if (replayTimer) {

        clearInterval(
            replayTimer
        );

        replayTimer = null;
    }
}


// ============================================================
// PLAY / PAUSE
// ============================================================

function toggleReplay() {

    if (replayTimer) {

        stopReplay();

        setPlayButton(
            "▶ PLAY"
        );

    }

    else {

        startReplay();

        setPlayButton(
            "⏸ PAUSE"
        );
    }
}


// ============================================================
// PLAY BUTTON
// ============================================================

function setPlayButton(text) {

    const button =
        document.getElementById(
            "play-button"
        );


    if (button) {

        button.textContent =
            text;
    }
}


// ============================================================
// REPLAY SPEED
// ============================================================

function setReplaySpeed(speed) {

    replaySpeed =
        Number(speed);


    console.log(
        "RAPTOR: Replay speed:",
        replaySpeed + "x"
    );


    /*
     * Restart timer using the new speed.
     */

    if (replayTimer) {

        startReplay();
    }


    /*
     * Update active button.
     */

    document
        .querySelectorAll(
            ".speed-button"
        )
        .forEach(button => {

            button.classList.remove(
                "active"
            );


            if (
                Number(
                    button.dataset.speed
                ) === replaySpeed
            ) {

                button.classList.add(
                    "active"
                );
            }

        });
}


// ============================================================
// SETUP REPLAY SLIDER
// ============================================================

function setupTimeline() {

    const slider =
        document.getElementById(
            "replay-slider"
        );


    if (!slider) {

        console.warn(
            "RAPTOR: replay-slider not found."
        );

        return;
    }


    slider.min = 0;


    slider.max =
        Math.max(
            0,
            replayData.length - 1
        );


    slider.value =
        currentIndex;


    /*
     * Use oninput instead of addEventListener
     * so duplicate handlers are impossible.
     */

    slider.oninput =
        function () {

            currentIndex =
                Number(
                    this.value
                );


            console.log(
                "RAPTOR: Slider moved:",
                currentIndex
            );


            if (
                replayData[
                    currentIndex
                ]
            ) {

                updateDashboard(
                    replayData[
                        currentIndex
                    ]
                );
            }
        };
}


// ============================================================
// UPDATE REPLAY POSITION
// ============================================================

function updateReplayPosition() {

    const slider =
        document.getElementById(
            "replay-slider"
        );


    const position =
        document.getElementById(
            "replay-position"
        );


    if (slider) {

        slider.value =
            currentIndex;
    }


    if (position) {

        position.textContent =
            `${currentIndex + 1} / ${replayData.length}`;
    }
}


// ============================================================
// STEP REPLAY
// ============================================================

function stepReplay(amount) {

    if (
        replayData.length === 0
    ) {

        return;
    }


    currentIndex +=
        Number(amount);


    /*
     * Keep index inside valid range.
     */

    currentIndex =
        Math.max(
            0,
            Math.min(
                currentIndex,
                replayData.length - 1
            )
        );


    console.log(
        "RAPTOR: Manual step:",
        currentIndex
    );


    updateDashboard(
        replayData[
            currentIndex
        ]
    );
}


// ============================================================
// JUMP TO NEXT RAPTOR ALERT
// ============================================================

function jumpToNextAlert() {

    if (
        replayData.length === 0
    ) {

        return;
    }


    console.log(
        "RAPTOR: Searching for next alert..."
    );


    for (
        let i = currentIndex + 1;
        i < replayData.length;
        i++
    ) {

        const probability =
            Number(
                replayData[i]
                    .attack_probability || 0
            );


        if (
            probability >=
            RAPTOR_THRESHOLD
        ) {

            currentIndex = i;


            console.log(
                "RAPTOR: Next alert found:",
                currentIndex,
                replayData[i].time_window,
                probability
            );


            updateDashboard(
                replayData[
                    currentIndex
                ]
            );


            return;
        }
    }


    console.log(
        "RAPTOR: No further alerts found."
    );
}


// ============================================================
// FORMAT TIMESTAMP
// ============================================================

function formatTime(timestamp) {

    if (
        !timestamp ||
        timestamp === "nan" ||
        timestamp === "NaT" ||
        timestamp === "null" ||
        timestamp === "undefined"
    ) {

        return "--:--:--";
    }


    const value =
        String(timestamp);


    /*
     * Example:
     *
     * 2018-02-14 01:01:40
     *
     * becomes:
     *
     * 01:01:40
     */

    const parts =
        value.split(" ");


    if (
        parts.length >= 2
    ) {

        return parts[1];
    }


    return value;
}


// ============================================================
// KEYBOARD CONTROLS
// ============================================================

document.addEventListener(
    "keydown",
    function (event) {


        // Space = Play / Pause

        if (
            event.code ===
            "Space"
        ) {

            /*
             * Don't interfere with text inputs.
             */

            if (
                event.target.tagName ===
                    "INPUT" ||
                event.target.tagName ===
                    "TEXTAREA"
            ) {

                return;
            }


            event.preventDefault();


            toggleReplay();
        }


        // Arrow Right = next state

        if (
            event.code ===
            "ArrowRight"
        ) {

            stepReplay(1);
        }


        // Arrow Left = previous state

        if (
            event.code ===
            "ArrowLeft"
        ) {

            stepReplay(-1);
        }

    }
);


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "===================================="
        );

        console.log(
            "RAPTOR Dashboard Loaded"
        );

        console.log(
            "Replay + Five-Step Forecast"
        );

        console.log(
            "Alert Threshold:",
            RAPTOR_THRESHOLD
        );

        console.log(
            "===================================="
        );


        loadReplay();
    }
);