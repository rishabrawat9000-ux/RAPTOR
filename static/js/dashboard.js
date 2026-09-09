let replayData = [];
let currentIndex = 0;
let replayTimer = null;
let replaySpeed = 1;

// =====================================================
// RAPTOR ALERT THRESHOLD
// =====================================================

const RAPTOR_THRESHOLD = 0.05;


// =====================================================
// LOAD REPLAY
// =====================================================

async function loadReplay() {

    console.log("RAPTOR: Loading replay...");

    try {

        const response = await fetch("/api/replay");

        if (!response.ok) {
            throw new Error("Replay API failed");
        }

        const data = await response.json();

        replayData = data.predictions || [];

        console.log(
            "RAPTOR replay loaded:",
            replayData.length,
            "predictions"
        );

        if (replayData.length === 0) {
            return;
        }

        setupTimeline();

        updateDashboard(replayData[0]);

    } catch (error) {

        console.error(
            "RAPTOR replay error:",
            error
        );
    }
}


// =====================================================
// UPDATE DASHBOARD
// =====================================================

function updateDashboard(prediction) {

    const attackProbability =
        Number(prediction.attack_probability || 0);

    const attackRatio =
        Number(prediction.attack_ratio || 0);

    const confidence =
        Number(prediction.stage_confidence || 0);


    document.getElementById(
        "attack-probability"
    ).textContent =
        (attackProbability * 100).toFixed(2) + "%";


    document.getElementById(
        "attack-ratio"
    ).textContent =
        (attackRatio * 100).toFixed(2) + "%";


    document.getElementById(
        "attack-stage"
    ).textContent =
        prediction.attack_stage || "Unknown";


    document.getElementById(
        "stage-confidence"
    ).textContent =
        (confidence * 100).toFixed(2) + "%";


    document.getElementById(
        "forecast-time"
    ).textContent =
        formatTime(prediction.time_window);


    updateThreatStatus(
        attackProbability
    );


    updateReplayPosition();
}


// =====================================================
// THREAT STATUS
// =====================================================

function updateThreatStatus(probability) {

    const status =
        document.getElementById(
            "threat-status"
        );

    if (!status) {
        return;
    }


    // High-risk condition
    if (probability >= 0.70) {

        status.textContent = "HIGH RISK";
        status.style.color = "#ff6b6b";

    }

    // Elevated condition
    else if (probability >= 0.30) {

        status.textContent = "ELEVATED";
        status.style.color = "#e8c66d";

    }

    // RAPTOR early-warning threshold
    else if (probability >= RAPTOR_THRESHOLD) {

        status.textContent = "RAPTOR ALERT";
        status.style.color = "#e8c66d";

    }

    // Below alert threshold
    else {

        status.textContent = "LOW RISK";
        status.style.color = "#70d99a";
    }
}


// =====================================================
// PLAY / PAUSE
// =====================================================

function startReplay() {

    stopReplay();

    replayTimer = setInterval(() => {

        if (currentIndex >= replayData.length - 1) {

            stopReplay();

            setPlayButton("▶ PLAY");

            return;
        }

        currentIndex++;

        updateDashboard(
            replayData[currentIndex]
        );

    }, 1000 / replaySpeed);
}


function stopReplay() {

    if (replayTimer) {

        clearInterval(replayTimer);
        replayTimer = null;
    }
}


function toggleReplay() {

    if (replayTimer) {

        stopReplay();

        setPlayButton("▶ PLAY");

    } else {

        startReplay();

        setPlayButton("⏸ PAUSE");
    }
}


function setPlayButton(text) {

    const button =
        document.getElementById(
            "play-button"
        );

    if (button) {
        button.textContent = text;
    }
}


// =====================================================
// SPEED
// =====================================================

function setReplaySpeed(speed) {

    replaySpeed = speed;

    if (replayTimer) {
        startReplay();
    }

    document.querySelectorAll(
        ".speed-button"
    ).forEach(button => {

        button.classList.remove("active");

        if (
            Number(button.dataset.speed)
            === speed
        ) {
            button.classList.add("active");
        }
    });
}


// =====================================================
// TIMELINE
// =====================================================

function setupTimeline() {

    const slider =
        document.getElementById(
            "replay-slider"
        );

    if (!slider) {
        return;
    }

    slider.min = 0;

    slider.max =
        replayData.length - 1;

    slider.value = 0;


    slider.addEventListener(
        "input",
        function () {

            currentIndex =
                Number(this.value);

            updateDashboard(
                replayData[currentIndex]
            );
        }
    );
}


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
        slider.value = currentIndex;
    }


    if (position) {

        position.textContent =
            `${currentIndex + 1} / ${replayData.length}`;
    }
}


// =====================================================
// STEP FORWARD / BACKWARD
// =====================================================

function stepReplay(amount) {

    if (replayData.length === 0) {
        return;
    }

    currentIndex += amount;


    currentIndex =
        Math.max(
            0,
            Math.min(
                currentIndex,
                replayData.length - 1
            )
        );


    updateDashboard(
        replayData[currentIndex]
    );
}


// =====================================================
// JUMP TO NEXT RAPTOR ALERT
// =====================================================

function jumpToNextAlert() {

    if (replayData.length === 0) {
        return;
    }


    const start =
        currentIndex + 1;


    // Search after current position
    for (
        let i = start;
        i < replayData.length;
        i++
    ) {

        const probability =
            Number(
                replayData[i]
                    .attack_probability || 0
            );


        if (probability >= RAPTOR_THRESHOLD) {

            currentIndex = i;

            updateDashboard(
                replayData[currentIndex]
            );

            return;
        }
    }


    // If no later alert exists,
    // search from the beginning
    for (
        let i = 0;
        i < start && i < replayData.length;
        i++
    ) {

        const probability =
            Number(
                replayData[i]
                    .attack_probability || 0
            );


        if (probability >= RAPTOR_THRESHOLD) {

            currentIndex = i;

            updateDashboard(
                replayData[currentIndex]
            );

            return;
        }
    }


    console.log(
        "No RAPTOR alerts found."
    );
}


// =====================================================
// TIME
// =====================================================

function formatTime(timestamp) {

    if (!timestamp) {
        return "--:--:--";
    }


    const parts =
        timestamp.split(" ");


    if (parts.length < 2) {
        return timestamp;
    }


    return parts[1];
}


// =====================================================
// INITIALIZE
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "RAPTOR dashboard loaded."
        );

        console.log(
            "RAPTOR alert threshold:",
            RAPTOR_THRESHOLD
        );

        loadReplay();

    }
);