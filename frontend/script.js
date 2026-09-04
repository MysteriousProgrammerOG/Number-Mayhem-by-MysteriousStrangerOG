/* ================================================
   NUMBER MAYHEM - Frontend Logic
   ================================================
   This file handles all the browser-side logic.
   It communicates with the Python backend using fetch().
   
   IMPORTANT: The browser NEVER decides game outcomes.
   All game logic (guesses, rewards, items, etc.)
   happens on the Python server.
   ================================================ */

// ================================================
// GLOBAL STATE
// ================================================

// Tracks the current game state from the server
let gameState = null;

// Tracks the player data from the server
let playerData = null;

// ================================================
// HELPER: API REQUEST FUNCTION
// ================================================

/**
 * Send a request to the backend API.
 * This is a helper function used by all the other functions.
 * 
 * @param {string} url      - The API endpoint (e.g. "/api/player")
 * @param {string} method   - "GET" or "POST"
 * @param {object} body     - Optional data to send (for POST requests)
 * @returns {Promise<object>} - The JSON response from the server
 */
async function apiRequest(url, method = "GET", body = null) {
    // Set up the request options
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    // If we have a body, add it to the request
    if (body) {
        options.body = JSON.stringify(body);
    }

    // Send the request and wait for the response
    const response = await fetch(url, options);

    // Parse the JSON response
    const data = await response.json();

    // If the server returned an error, throw it
    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}

// ================================================
// BOOT SEQUENCE
// ================================================

/**
 * Run the boot sequence animation.
 * Shows terminal-style boot lines, then reveals the game.
 */
function runBootSequence() {
    const bootScreen = document.getElementById("boot-screen");
    const bootLines = document.querySelectorAll(".boot-line");

    // Show each boot line one by one with a delay
    let delay = 0;
    bootLines.forEach((line, index) => {
        setTimeout(() => {
            line.classList.add("visible");
        }, delay);
        delay += 500; // 0.5 seconds between each line
    });

    // After all lines are shown, wait a moment then show the game
    setTimeout(() => {
        bootScreen.classList.add("hidden");
        document.getElementById("game-container").classList.remove("hidden");
        initGame();
    }, delay + 500);

    // Allow clicking to skip the boot sequence
    bootScreen.addEventListener("click", () => {
        bootScreen.classList.add("hidden");
        document.getElementById("game-container").classList.remove("hidden");
        initGame();
    });
}

// ================================================
// INITIALIZATION
// ================================================

/**
 * Initialize the game after the boot sequence.
 * Loads player data and sets up the interface.
 */
async function initGame() {
    try {
        // Load player data from the server
        playerData = await apiRequest("/api/player");
        updatePlayerBar();

        // Load the difficulty buttons
        loadDifficulties();

        // Check if there's an active game
        const gameStateResponse = await apiRequest("/api/game/state");
        if (gameStateResponse.active) {
            gameState = gameStateResponse.state;
            showGuessArea();
        } else {
            showDifficultySelect();
        }

        // Add event listener for the guess input (Enter key)
        document.getElementById("guess-input").addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                makeGuess();
            }
        });

        // Add event listener for the guess button
        document.getElementById("guess-button").addEventListener("click", makeGuess);

        // Print a welcome message to the terminal
        addOutputLine("SYSTEM: Welcome to NUMBER MAYHEM.", "system");
        addOutputLine("SYSTEM: Select a difficulty to begin.", "system");
    } catch (error) {
        addOutputLine(`ERROR: ${error.message}`, "red");
    }
}

// ================================================
// PLAYER BAR
// ================================================

/**
 * Update the player info bar at the top of the screen.
 */
function updatePlayerBar() {
    if (!playerData) return;

    document.getElementById("player-coins").textContent = playerData.coins;
    document.getElementById("player-streak").textContent = playerData.win_streak;
    document.getElementById("player-wins").textContent = playerData.games_won;
    document.getElementById("player-losses").textContent = playerData.games_lost;
}

// ================================================
// DIFFICULTY SELECTION
// ================================================

/**
 * Load the difficulty buttons into the grid.
 * The difficulty data comes from the server.
 */
async function loadDifficulties() {
    // Get the difficulty data from the server
    // (We use the shop endpoint's items as a reference, but difficulties
    //  are defined in the backend constants. We'll hardcode the display
    //  since the server validates the difficulty on game start anyway.)
    const difficulties = [
        { id: "baby", icon: "👶", name: "Baby", details: "1-10 | 10 attempts | 5🪙" },
        { id: "easy", icon: "🟢", name: "Easy", details: "1-50 | 8 attempts | 15🪙" },
        { id: "normal", icon: "🟡", name: "Normal", details: "1-1,000 | 10 attempts | 50🪙" },
        { id: "hard", icon: "🔴", name: "Hard", details: "1-10,000 | 8 attempts | 150🪙" },
        { id: "extreme", icon: "☠️", name: "Extreme", details: "1-1,000,000 | 10 attempts | 1,000🪙" },
        { id: "impossible", icon: "💀", name: "Impossible", details: "0.1-10,000 | 5 attempts | 10,000🪙" }
    ];

    const grid = document.getElementById("difficulty-grid");
    grid.innerHTML = "";

    // Create a button for each difficulty
    difficulties.forEach((diff) => {
        const button = document.createElement("button");
        button.className = "difficulty-button";
        button.innerHTML = `
            <span class="diff-icon">${diff.icon}</span>
            <span class="diff-name">${diff.name}</span>
            <span class="diff-details">${diff.details}</span>
        `;
        // When clicked, start a game on this difficulty
        button.addEventListener("click", () => startGame(diff.id));
        grid.appendChild(button);
    });
}

/**
 * Show the difficulty selection screen.
 */
function showDifficultySelect() {
    gameState = null;
    document.getElementById("difficulty-select").classList.remove("hidden");
    document.getElementById("guess-area").classList.add("hidden");
    document.getElementById("game-over-actions").classList.add("hidden");
    document.getElementById("game-difficulty").textContent = "NOT SELECTED";
    document.getElementById("game-range").textContent = "-";
    document.getElementById("game-attempts").textContent = "-";
    document.getElementById("game-decimals").textContent = "OFF";
    document.getElementById("game-streak-mult").textContent = "×1.0";
}

// ================================================
// GAME START
// ================================================

/**
 * Start a new game on the given difficulty.
 * Sends a request to the server, which generates the secret number.
 */
async function startGame(difficultyId) {
    try {
        addOutputLine(`> STARTING GAME ON ${difficultyId.toUpperCase()}...`, "cyan");

        // Tell the server to start a game
        const result = await apiRequest("/api/game/start", "POST", {
            difficulty: difficultyId
        });

        // Store the game state
        gameState = result.state;

        // Update the UI
        updateGameInfo();
        showGuessArea();
        addOutputLine(`> GAME STARTED: ${gameState.difficulty_name} difficulty.`, "green");
        addOutputLine(`> RANGE: ${gameState.low} - ${gameState.high}`, "cyan");
        addOutputLine(`> ATTEMPTS: ${gameState.max_attempts}`, "cyan");
        if (gameState.decimals) {
            addOutputLine("> DECIMALS: ENABLED", "yellow");
        }
        addOutputLine("> AWAITING INPUT...", "dim");

        // Focus the guess input
        document.getElementById("guess-input").focus();
    } catch (error) {
        addOutputLine(`ERROR: ${error.message}`, "red");
    }
}

/**
 * Show the guess input area.
 */
function showGuessArea() {
    document.getElementById("difficulty-select").classList.add("hidden");
    document.getElementById("guess-area").classList.remove("hidden");
    document.getElementById("game-over-actions").classList.add("hidden");
    updateItemButtons();
}

/**
 * Update the game info panel with the current state.
 */
function updateGameInfo() {
    if (!gameState) return;

    document.getElementById("game-difficulty").textContent = `${gameState.difficulty_icon} ${gameState.difficulty_name}`;
    document.getElementById("game-range").textContent = `${gameState.low} - ${gameState.high}`;
    document.getElementById("game-attempts").textContent = `${gameState.attempts} / ${gameState.max_attempts}`;
    document.getElementById("game-decimals").textContent = gameState.decimals ? "ON" : "OFF";
    document.getElementById("game-streak-mult").textContent = `×${gameState.streak_multiplier.toFixed(1)}`;
}

// ================================================
// GUESSING
// ================================================

/**
 * Send the player's guess to the server.
 * The server decides if it's correct, too high, or too low.
 */
async function makeGuess() {
    const input = document.getElementById("guess-input");
    const rawValue = input.value.trim();

    // Don't send empty guesses
    if (!rawValue) {
        addOutputLine("> ERROR: ENTER A NUMBER FIRST.", "red");
        return;
    }

    // Parse the guess as a number
    const guess = parseFloat(rawValue);

    // Check it's actually a number
    if (isNaN(guess)) {
        addOutputLine("> ERROR: INVALID NUMBER.", "red");
        input.value = "";
        return;
    }

    // Disable the button while waiting for the server
    const button = document.getElementById("guess-button");
    button.disabled = true;

    try {
        addOutputLine(`> EXECUTING GUESS...`, "cyan");
        addOutputLine(`> INPUT: ${guess}`, "white");

        // Send the guess to the server
        const result = await apiRequest("/api/game/guess", "POST", {
            guess: guess
        });

        // Update game state
        gameState = result.state;

        // Handle the result
        if (result.correct) {
            // WIN!
            handleWin(result);
        } else if (result.game_over) {
            // LOSS!
            handleLoss(result);
        } else {
            // Wrong guess, game continues
            addOutputLine(`> ANALYZING...`, "cyan");
            if (result.feedback === "too_low") {
                addOutputLine("> RESULT: NUMBER TOO LOW", "yellow");
                addOutputLine("> INCREASE VALUE.", "yellow");
            } else {
                addOutputLine("> RESULT: NUMBER TOO HIGH", "yellow");
                addOutputLine("> DECREASE VALUE.", "yellow");
            }
            updateGameInfo();
            updateItemButtons();
        }

        // Clear the input
        input.value = "";
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    } finally {
        // Re-enable the button
        button.disabled = false;
        input.focus();
    }
}

// ================================================
// WIN / LOSE HANDLING
// ================================================

/**
 * Handle a winning guess.
 * Shows the reward breakdown and any new achievements.
 */
async function handleWin(result) {
    addOutputLine("", "dim");
    addOutputLine("> ACCESS GRANTED", "green");
    addOutputLine("> NUMBER IDENTIFIED", "green");
    addOutputLine(`> TARGET: ${result.secret_number}`, "white");
    addOutputLine("> GAME COMPLETE", "green");
    addOutputLine("", "dim");

    // Show reward breakdown
    const breakdown = result.reward_breakdown;
    addOutputLine("═══════ REWARD BREAKDOWN ═══════", "gold");
    addOutputLine(`  BASE REWARD:        ${breakdown.base_reward} 🪙`, "gold");
    if (breakdown.attempts_bonus > 0) {
        addOutputLine(`  ATTEMPTS REMAINING: +${breakdown.attempts_bonus} 🪙`, "gold");
    }
    if (breakdown.perfect_bonus > 0) {
        addOutputLine(`  PERFECT GAME:       +${breakdown.perfect_bonus} 🪙`, "gold");
    }
    addOutputLine(`  STREAK MULTIPLIER:  ×${breakdown.streak_multiplier.toFixed(1)}`, "gold");
    if (breakdown.double_reward) {
        addOutputLine("  DOUBLE REWARD:      ×2", "gold");
    }
    addOutputLine("  ─────────────────────────────", "gold");
    addOutputLine(`  TOTAL:              ${breakdown.total} 🪙`, "gold");
    addOutputLine("", "dim");

    // Show new achievements
    if (result.new_achievements && result.new_achievements.length > 0) {
        result.new_achievements.forEach((achId) => {
            showAchievementPopup(achId);
        });
    }

    // Update player data
    playerData = await apiRequest("/api/player");
    updatePlayerBar();

    // Show game over actions
    document.getElementById("guess-area").classList.add("hidden");
    document.getElementById("game-over-actions").classList.remove("hidden");
    addOutputLine("> SELECT AN ACTION TO CONTINUE.", "system");
}

/**
 * Handle running out of attempts.
 */
async function handleLoss(result) {
    addOutputLine("", "dim");
    addOutputLine("> ACCESS DENIED", "red");
    addOutputLine("> ATTEMPTS EXHAUSTED", "red");
    addOutputLine(`> TARGET WAS: ${result.secret_number}`, "white");
    addOutputLine("> GAME OVER", "red");
    addOutputLine("", "dim");

    if (result.streak_shield_active) {
        addOutputLine("> STREAK SHIELD PROTECTED YOUR STREAK!", "green");
    } else if (result.streak_lost) {
        addOutputLine("> STREAK LOST!", "red");
    }

    // Update player data
    playerData = await apiRequest("/api/player");
    updatePlayerBar();

    // Show game over actions
    document.getElementById("guess-area").classList.add("hidden");
    document.getElementById("game-over-actions").classList.remove("hidden");
    addOutputLine("> SELECT AN ACTION TO CONTINUE.", "system");
}

// ================================================
// ITEMS
// ================================================

/**
 * Update the item buttons shown during gameplay.
 * Only shows buttons for items the player actually owns.
 */
function updateItemButtons() {
    const container = document.getElementById("item-buttons");
    container.innerHTML = "";

    // If there's no active game, don't show item buttons
    if (!gameState || gameState.game_over) return;

    // Check if the player has any items
    if (!playerData) return;

    const inventory = playerData.inventory;
    const itemDefinitions = [
        { id: "hint", icon: "🔮", name: "Hint" },
        { id: "free_guess", icon: "🎟️", name: "Free Guess" },
        { id: "reveal_digit", icon: "🔍", name: "Reveal Digit" },
        { id: "double_reward", icon: "💰", name: "Double Reward" },
        { id: "lucky_guess", icon: "🎲", name: "Lucky Guess" },
        { id: "streak_shield", icon: "🛡️", name: "Streak Shield" }
    ];

    // Create a button for each item the player owns
    itemDefinitions.forEach((item) => {
        const count = inventory[item.id] || 0;
        if (count > 0) {
            const button = document.createElement("button");
            button.className = "item-button";
            button.textContent = `${item.icon} ${item.name} (${count})`;
            button.addEventListener("click", () => useItem(item.id));
            container.appendChild(button);
        }
    });
}

/**
 * Use an item during the game.
 * Sends the request to the server, which validates ownership.
 */
async function useItem(itemId) {
    try {
        addOutputLine(`> USING ITEM: ${itemId.toUpperCase()}...`, "magenta");

        // Send the item use request to the server
        const result = await apiRequest("/api/game/use-item", "POST", {
            item_id: itemId
        });

        // Update game state
        gameState = result.state;

        // Handle the item result
        if (result.item === "hint") {
            addOutputLine(`> ${result.hint_text}`, "magenta");
        } else if (result.item === "free_guess") {
            addOutputLine(`> ${result.message}`, "green");
        } else if (result.item === "reveal_digit") {
            addOutputLine(`> REVEALED: ${result.revealed}`, "magenta");
        } else if (result.item === "double_reward") {
            addOutputLine(`> ${result.message}`, "gold");
        } else if (result.item === "lucky_guess") {
            addOutputLine(`> LUCKY GUESS PICKED: ${result.lucky_guess_value}`, "magenta");
            if (result.lucky_guess_correct) {
                addOutputLine("> LUCKY! THAT'S THE NUMBER!", "green");
                handleWin(result);
                return;
            } else {
                addOutputLine("> UNLUCKY! THAT GUESS WAS WRONG.", "red");
                if (result.game_over) {
                    handleLoss(result);
                    return;
                }
            }
        } else if (result.item === "streak_shield") {
            addOutputLine(`> ${result.message}`, "green");
        }

        // Update player data (inventory changed)
        playerData = await apiRequest("/api/player");
        updatePlayerBar();
        updateGameInfo();
        updateItemButtons();
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    }
}

// ================================================
// OUTPUT TERMINAL
// ================================================

/**
 * Add a line of text to the output terminal.
 * 
 * @param {string} text  - The text to display
 * @param {string} color - The CSS class for color (dim, green, cyan, gold, red, magenta, yellow, white, system)
 */
function addOutputLine(text, color = "dim") {
    const terminal = document.getElementById("output-terminal");

    // Create a new line element
    const line = document.createElement("div");
    line.className = `output-line ${color}`;
    line.textContent = text;

    // Add it to the terminal
    terminal.appendChild(line);

    // Scroll to the bottom
    terminal.scrollTop = terminal.scrollHeight;
}

// ================================================
// SHOP
// ================================================

/**
 * Open the shop modal and load the shop items.
 */
async function openShop() {
    try {
        // Get shop data from the server
        const shopData = await apiRequest("/api/shop");

        // Update the coins display
        document.getElementById("shop-coins").textContent = `CREDITS: ${shopData.coins}`;

        // Build the shop item list
        const body = document.getElementById("shop-body");
        body.innerHTML = "";

        // Create an entry for each item
        Object.entries(shopData.items).forEach(([itemId, item]) => {
            const count = shopData.inventory[itemId] || 0;

            const itemDiv = document.createElement("div");
            itemDiv.className = "shop-item";
            itemDiv.innerHTML = `
                <div class="shop-item-info">
                    <div class="shop-item-name">${item.icon} ${item.name}</div>
                    <div class="shop-item-desc">${item.description}</div>
                </div>
                <div class="shop-item-count">OWNED: ${count}</div>
                <div class="shop-item-cost">${item.cost} 🪙</div>
                <button class="shop-buy-button" data-item="${itemId}">BUY</button>
            `;

            // Add the buy button click handler
            const buyButton = itemDiv.querySelector(".shop-buy-button");
            buyButton.addEventListener("click", () => buyItem(itemId));

            body.appendChild(itemDiv);
        });

        // Show the modal
        document.getElementById("shop-modal").classList.remove("hidden");
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    }
}

/**
 * Buy an item from the shop.
 * The server validates the purchase.
 */
async function buyItem(itemId) {
    try {
        // Send the purchase request to the server
        const result = await apiRequest("/api/shop/buy", "POST", {
            item_id: itemId
        });

        // Update player data
        playerData = result.player;
        updatePlayerBar();

        // Show a success message
        addOutputLine(`> ${result.message}`, "green");

        // Refresh the shop display
        openShop();
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    }
}

// ================================================
// INVENTORY
// ================================================

/**
 * Open the inventory modal.
 */
async function openInventory() {
    try {
        // Get the latest player data
        playerData = await apiRequest("/api/player");

        const body = document.getElementById("inventory-body");
        body.innerHTML = "";

        const inventory = playerData.inventory;
        const itemDefinitions = [
            { id: "hint", icon: "🔮", name: "Hint", desc: "Reveals a clue about the number." },
            { id: "free_guess", icon: "🎟️", name: "Free Guess", desc: "Guess without using an attempt." },
            { id: "reveal_digit", icon: "🔍", name: "Reveal Digit", desc: "Reveals one digit of the secret number." },
            { id: "double_reward", icon: "💰", name: "Double Reward", desc: "Doubles the coins you earn on a win." },
            { id: "lucky_guess", icon: "🎲", name: "Lucky Guess", desc: "Auto-guesses with 50% hit chance." },
            { id: "streak_shield", icon: "🛡️", name: "Streak Shield", desc: "Protects your win streak from a loss." }
        ];

        let hasItems = false;

        // Create an entry for each item the player owns
        itemDefinitions.forEach((item) => {
            const count = inventory[item.id] || 0;
            if (count > 0) {
                hasItems = true;

                const itemDiv = document.createElement("div");
                itemDiv.className = "inventory-item";
                itemDiv.innerHTML = `
                    <div class="inventory-item-info">
                        <div class="inventory-item-name">${item.icon} ${item.name}</div>
                        <div class="inventory-item-desc">${item.desc}</div>
                    </div>
                    <div class="inventory-item-count">× ${count}</div>
                    <button class="inventory-use-button" data-item="${item.id}">USE</button>
                `;

                // Add the use button click handler
                const useButton = itemDiv.querySelector(".inventory-use-button");
                useButton.addEventListener("click", () => {
                    closeModal("inventory-modal");
                    useItem(item.id);
                });

                body.appendChild(itemDiv);
            }
        });

        // Show a message if the inventory is empty
        if (!hasItems) {
            body.innerHTML = '<div class="empty-message">INVENTORY EMPTY. VISIT THE SHOP TO BUY ITEMS.</div>';
        }

        // Show the modal
        document.getElementById("inventory-modal").classList.remove("hidden");
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    }
}

// ================================================
// STATS
// ================================================

/**
 * Open the stats modal.
 */
async function openStats() {
    try {
        // Get the latest player data
        playerData = await apiRequest("/api/player");

        const body = document.getElementById("stats-body");
        body.innerHTML = "";

        // Build the stats grid
        body.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-label">CREDITS</span>
                    <span class="stat-value gold">${playerData.coins} 🪙</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">TOTAL COINS EARNED</span>
                    <span class="stat-value gold">${playerData.total_coins_earned} 🪙</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">GAMES WON</span>
                    <span class="stat-value green">${playerData.games_won}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">GAMES LOST</span>
                    <span class="stat-value red">${playerData.games_lost}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">WIN STREAK</span>
                    <span class="stat-value yellow">${playerData.win_streak} 🔥</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">HIGHEST STREAK</span>
                    <span class="stat-value yellow">${playerData.highest_streak} 🔥</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">PERFECT GAMES</span>
                    <span class="stat-value cyan">${playerData.perfect_games} 🎯</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">ITEMS USED</span>
                    <span class="stat-value magenta">${playerData.items_used} 🧪</span>
                </div>
            </div>
            <div class="stats-section">
                <div class="stats-section-title">DIFFICULTY WINS</div>
                <div class="difficulty-stat"><span class="label">👶 Baby</span><span class="value">${playerData.difficulty_wins.baby || 0}</span></div>
                <div class="difficulty-stat"><span class="label">🟢 Easy</span><span class="value">${playerData.difficulty_wins.easy || 0}</span></div>
                <div class="difficulty-stat"><span class="label">🟡 Normal</span><span class="value">${playerData.difficulty_wins.normal || 0}</span></div>
                <div class="difficulty-stat"><span class="label">🔴 Hard</span><span class="value">${playerData.difficulty_wins.hard || 0}</span></div>
                <div class="difficulty-stat"><span class="label">☠️ Extreme</span><span class="value">${playerData.difficulty_wins.extreme || 0}</span></div>
                <div class="difficulty-stat"><span class="label">💀 Impossible</span><span class="value">${playerData.difficulty_wins.impossible || 0}</span></div>
            </div>
        `;

        // Show the modal
        document.getElementById("stats-modal").classList.remove("hidden");
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    }
}

// ================================================
// ACHIEVEMENTS
// ================================================

/**
 * Open the achievements modal.
 */
async function openAchievements() {
    try {
        // Get achievements from the server
        const data = await apiRequest("/api/achievements");

        const body = document.getElementById("achievements-body");
        body.innerHTML = "";

        // Create an entry for each achievement
        data.achievements.forEach((ach) => {
            const achDiv = document.createElement("div");
            achDiv.className = `achievement-item ${ach.unlocked ? "unlocked" : "locked"}`;
            achDiv.innerHTML = `
                <div class="achievement-icon">${ach.icon}</div>
                <div class="achievement-info">
                    <div class="achievement-name">${ach.name}</div>
                    <div class="achievement-desc">${ach.description}</div>
                </div>
                <div class="achievement-status">${ach.unlocked ? "UNLOCKED ✓" : "LOCKED"}</div>
            `;
            body.appendChild(achDiv);
        });

        // Show the modal
        document.getElementById("achievements-modal").classList.remove("hidden");
    } catch (error) {
        addOutputLine(`> ERROR: ${error.message}`, "red");
    }
}

/**
 * Show a temporary achievement unlock notification.
 */
function showAchievementPopup(achievementId) {
    // Get the achievement data from the server
    apiRequest("/api/achievements").then((data) => {
        const ach = data.achievements.find((a) => a.id === achievementId);
        if (!ach) return;

        // Set the popup content
        document.getElementById("achievement-popup-icon").textContent = ach.icon;
        document.getElementById("achievement-popup-name").textContent = ach.name;
        document.getElementById("achievement-popup-desc").textContent = ach.description;

        // Show the popup
        const popup = document.getElementById("achievement-popup");
        popup.classList.remove("hidden");

        // Hide it after 3 seconds
        setTimeout(() => {
            popup.classList.add("hidden");
        }, 3000);
    });
}

// ================================================
// MODAL HELPERS
// ================================================

/**
 * Close a modal by its ID.
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
}

// ================================================
// START THE GAME
// ================================================

// Run the boot sequence when the page loads
window.addEventListener("load", () => {
    runBootSequence();
});