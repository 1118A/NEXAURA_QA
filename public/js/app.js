// Initialize Theme Selection based on server time or cached user override
const savedTheme = localStorage.getItem("theme");
const timeTheme = document.documentElement.getAttribute("data-time-theme");
const activeTheme = savedTheme || timeTheme || "dark";

if (activeTheme === "light") {
    document.documentElement.classList.add("light-mode");
} else {
    document.documentElement.classList.remove("light-mode");
}

// Initialize Weather Theme early to prevent style flashing
let savedWeather = localStorage.getItem("weather") || "auto";
applyWeatherTheme(savedWeather);

function applyWeatherTheme(weather) {
    // Remove existing weather classes
    document.documentElement.classList.remove("weather-sunny", "weather-rainy", "weather-winter", "weather-cloudy");
    
    let activeWeather = weather;
    if (weather === "auto") {
        // Read recommended weather computed by python datetime library on the server
        const timeWeather = document.documentElement.getAttribute("data-time-weather");
        activeWeather = timeWeather || "sunny";
    }
    
    document.documentElement.classList.add(`weather-${activeWeather}`);
    updateWeatherGraphic(activeWeather);
}

// Configure Backend API URL Input
document.addEventListener("DOMContentLoaded", () => {
    const backendUrlInput = document.getElementById("backend-url-input");
    const healthBadge = document.querySelector(".health-badge");
    
    function updateHealthBadge(url) {
        if (healthBadge && url) {
            healthBadge.href = `${url.replace(/\/$/, "")}/health`;
        } else if (healthBadge) {
            healthBadge.href = "/health";
        }
    }
    
    if (backendUrlInput) {
        const savedUrl = localStorage.getItem("backend_url") || "";
        backendUrlInput.value = savedUrl;
        updateHealthBadge(savedUrl);
        
        backendUrlInput.addEventListener("change", () => {
            let val = backendUrlInput.value.trim();
            if (val && !val.startsWith("http://") && !val.startsWith("https://")) {
                val = "https://" + val;
                backendUrlInput.value = val;
            }
            localStorage.setItem("backend_url", val);
            updateHealthBadge(val);
            showToast("Backend API URL updated!", "success");
        });
    }
});


function getApiUrl(endpoint) {
    const configuredUrl = localStorage.getItem("backend_url");
    if (configuredUrl) {
        return `${configuredUrl.replace(/\/$/, "")}${endpoint}`;
    }
    return endpoint;
}

// Initialize Lucide Icons & Particles
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initThemeParticles();
    
    // Initial weather graphic render once DOM is ready
    const currentActiveWeather = getActiveWeatherName();
    updateWeatherGraphic(currentActiveWeather);
    
    // Theme Toggle Handler
    const themeToggleBtn = document.getElementById("theme-toggle");
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            document.documentElement.classList.toggle("light-mode");
            if (document.documentElement.classList.contains("light-mode")) {
                localStorage.setItem("theme", "light");
                showToast("Light mode activated", "success");
            } else {
                localStorage.setItem("theme", "dark");
                showToast("Dark mode activated", "success");
            }
        });
    }

    // Custom Weather Dropdown Handler
    const dropdownWrap = document.getElementById("weather-dropdown-container");
    const dropdownTrigger = document.getElementById("weather-dropdown-trigger");
    const dropdownMenu = document.getElementById("weather-dropdown-menu");
    
    if (dropdownWrap && dropdownTrigger && dropdownMenu) {
        const currentText = dropdownWrap.querySelector(".current-weather-text");
        const currentIcon = dropdownWrap.querySelector(".current-weather-icon");
        const dropdownItems = dropdownWrap.querySelectorAll(".dropdown-item");
        
        const weatherIcons = {
            "auto": "refresh-cw",
            "sunny": "sun",
            "rainy": "umbrella",
            "winter": "snowflake",
            "cloudy": "cloud"
        };
        
        // Toggle dropdown open state
        dropdownTrigger.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdownWrap.classList.toggle("open");
            dropdownTrigger.setAttribute("aria-expanded", dropdownWrap.classList.contains("open"));
        });
        
        // Close dropdown when clicking outside
        document.addEventListener("click", () => {
            dropdownWrap.classList.remove("open");
            dropdownTrigger.setAttribute("aria-expanded", "false");
        });
        
        // Handle item selection
        dropdownItems.forEach(item => {
            const val = item.getAttribute("data-value");
            
            // Set initial active state based on savedWeather
            if (val === savedWeather) {
                dropdownItems.forEach(i => i.classList.remove("active"));
                item.classList.add("active");
                currentText.textContent = item.textContent.trim();
                const iconName = weatherIcons[val] || "sun";
                currentIcon.outerHTML = `<i data-lucide="${iconName}" class="current-weather-icon"></i>`;
            }
            
            item.addEventListener("click", () => {
                dropdownItems.forEach(i => i.classList.remove("active"));
                item.classList.add("active");
                currentText.textContent = item.textContent.trim();
                const iconName = weatherIcons[val] || "sun";
                
                const triggerIcon = dropdownWrap.querySelector(".current-weather-icon");
                if (triggerIcon) {
                    triggerIcon.outerHTML = `<i data-lucide="${iconName}" class="current-weather-icon"></i>`;
                }
                
                // Re-trigger Lucide icon instantiation
                if (window.lucide) {
                    lucide.createIcons();
                }
                
                localStorage.setItem("weather", val);
                savedWeather = val;
                applyWeatherTheme(val);
                showToast(`Weather theme: ${val.toUpperCase()}`, "success");
            });
        });
        
        // Re-trigger Lucide initially to build the correct icon in trigger
        if (window.lucide) {
            lucide.createIcons();
        }
    }
});

// DOM Elements
const indexForm = document.getElementById("index-form");
const repoUrlInput = document.getElementById("repo_url");
const btnIndex = document.getElementById("btn-index");
const indexLoader = document.getElementById("index-loader");
const indexSuccess = document.getElementById("index-success");
const metricFiles = document.getElementById("metric-files");
const metricChunks = document.getElementById("metric-chunks");

const askForm = document.getElementById("ask-form");
const questionInput = document.getElementById("question");
const topKInput = document.getElementById("top_k");
const thresholdInput = document.getElementById("similarity_threshold");
const btnAsk = document.getElementById("btn-ask");
const qaLoader = document.getElementById("qa-loader");
const answerContainer = document.getElementById("answer-container");
const answerBody = document.getElementById("answer-body");
const citationsList = document.getElementById("citations-list");
const btnCopyAnswer = document.getElementById("btn-copy-answer");
const toastContainer = document.getElementById("toast-container");

let currentGeneratedAnswerText = "";

// ----------------------------------------------------
// UI Helpers
// ----------------------------------------------------

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let iconName = "info";
    if (type === "success") iconName = "check-circle";
    if (type === "error") iconName = "alert-triangle";
    if (type === "warning") iconName = "alert-circle";

    toast.innerHTML = `
        <span class="toast-icon"><i data-lucide="${iconName}"></i></span>
        <div class="toast-content">${escapeHtml(message)}</div>
    `;

    toastContainer.appendChild(toast);
    lucide.createIcons({ attrs: { class: 'lucide-icon' } });

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(20px)";
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

function copyToClipboard(text, successMsg) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg, "success");
    }).catch(err => {
        showToast("Clipboard copy failed: " + err, "error");
    });
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Secure lightweight Markdown parser for formatting answers
function parseMarkdown(text) {
    if (!text) return "";

    // Escape HTML to prevent XSS (excluding code blocks and tags we will inject)
    let html = escapeHtml(text);

    // Restoring markers for formatting blocks

    // 1. Code blocks: ```[lang]\ncode\n```
    html = html.replace(/&lt;pre&gt;&lt;code class=&quot;language-([\s\S]*?)&quot;&gt;([\s\S]*?)&lt;\/code&gt;&lt;\/pre&gt;/g, '<pre><code class="language-$1">$2</code></pre>'); // Safety recovery
    html = html.replace(/```(\w*)\n([\s\S]*?)\n```/g, function (match, lang, code) {
        return `<pre><code class="language-${lang}">${code}</code></pre>`;
    });

    // 2. Inline code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 3. Bold: **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 4. Linebreaks inside paragraph blocks
    let lines = html.split("\n\n");
    let formattedLines = lines.map(line => {
        if (line.trim().startsWith("<pre>")) return line;
        return `<p>${line.replace(/\n/g, "<br>")}</p>`;
    });

    return formattedLines.join("");
}

// ----------------------------------------------------
// AJAX Events
// ----------------------------------------------------

// Form: Repo Indexing
indexForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const repoUrl = repoUrlInput.value.trim();
    if (!repoUrl) {
        showToast("Please enter a valid repository URL.", "warning");
        return;
    }

    // Toggle state
    btnIndex.disabled = true;
    repoUrlInput.disabled = true;
    indexSuccess.classList.add("hidden");
    indexLoader.classList.remove("hidden");

    // Disable Ask Controls until indexing completes
    questionInput.disabled = true;
    btnAsk.disabled = true;

    showToast("Cloning repository, parsing AST structures, and writing vector indices...", "info");

    try {
        const response = await fetch(getApiUrl("/index"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ repo_url: repoUrl })
        });

        const json = await response.json();

        if (response.ok && json.success) {
            metricFiles.innerText = json.files_indexed;
            metricChunks.innerText = json.chunks_indexed;

            indexSuccess.classList.remove("hidden");
            showToast(json.message || "Indexing completed successfully!", "success");

            // Enable Ask controls
            questionInput.disabled = false;
            btnAsk.disabled = false;
        } else {
            showToast(json.error || "An error occurred while indexing.", "error");
        }
    } catch (err) {
        showToast("Network connection error. Server might be offline.", "error");
        console.error(err);
    } finally {
        indexLoader.classList.add("hidden");
        btnIndex.disabled = false;
        repoUrlInput.disabled = false;
    }
});

// Form: Ask Question
askForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = questionInput.value.trim();
    const top_k = parseInt(topKInput.value);
    const threshold = parseFloat(thresholdInput.value);

    if (!question) {
        showToast("Please enter a question.", "warning");
        return;
    }

    btnAsk.disabled = true;
    questionInput.disabled = true;
    answerContainer.classList.add("hidden");
    qaLoader.classList.remove("hidden");

    try {
        const response = await fetch(getApiUrl("/ask"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                top_k: top_k,
                similarity_threshold: threshold
            })
        });

        const json = await response.json();

        if (response.ok && json.success) {
            currentGeneratedAnswerText = json.answer;
            answerBody.innerHTML = parseMarkdown(json.answer);

            // Render citations
            citationsList.innerHTML = "";
            if (json.sources && json.sources.length > 0) {
                json.sources.forEach((source, index) => {
                    const symbolBadge = source.symbol_name
                        ? `<span class="citation-badge">${escapeHtml(source.symbol_type)}: ${escapeHtml(source.symbol_name)}</span>`
                        : "";

                    const citationCard = document.createElement("div");
                    citationCard.className = "citation-card";
                    citationCard.innerHTML = `
                        <div class="citation-summary" data-index="${index}">
                            <div class="citation-meta">
                                <span class="citation-file">${escapeHtml(source.relative_path)}</span>
                                <span class="citation-lines">${source.start_line}-${source.end_line}</span>
                                ${symbolBadge}
                            </div>
                            <div style="display:flex; align-items:center; gap:12px;">
                                <span class="citation-score">Score: ${source.score.toFixed(3)}</span>
                                <span class="citation-action-icon"><i data-lucide="chevron-down"></i></span>
                            </div>
                        </div>
                        <div class="citation-details">
                            <div class="citation-code-wrap">
                                <button class="btn-icon-label btn-copy-citation" data-index="${index}">
                                    <i data-lucide="copy"></i> Copy
                                </button>
                                <pre><code>${escapeHtml(source.content)}</code></pre>
                            </div>
                        </div>
                    `;

                    // Toggle expand/collapse
                    const summary = citationCard.querySelector(".citation-summary");
                    summary.addEventListener("click", () => {
                        citationCard.classList.toggle("expanded");
                    });

                    // Copy specific code citation snippet
                    const copyBtn = citationCard.querySelector(".btn-copy-citation");
                    copyBtn.addEventListener("click", (evt) => {
                        evt.stopPropagation(); // Avoid folding trigger
                        copyToClipboard(source.content, `Citation ${source.relative_path}:${source.start_line}-${source.end_line} copied!`);
                    });

                    citationsList.appendChild(citationCard);
                });
            } else {
                citationsList.innerHTML = '<p class="loader-text" style="text-align:left; color: var(--text-muted);">No matching sources met the similarity threshold.</p>';
            }

            // Re-render Lucide Icons for dynamic content
            lucide.createIcons();

            answerContainer.classList.remove("hidden");
            showToast("Answer generated successfully.", "success");

            // Smooth scroll down to answer
            setTimeout(() => {
                answerContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 100);

        } else {
            showToast(json.error || "An error occurred while retrieving answers.", "error");
        }
    } catch (err) {
        showToast("Network connection error. Server might be offline.", "error");
        console.error(err);
    } finally {
        qaLoader.classList.add("hidden");
        btnAsk.disabled = false;
        questionInput.disabled = false;
    }
});

// Copy whole answer text
btnCopyAnswer.addEventListener("click", () => {
    if (!currentGeneratedAnswerText) return;
    copyToClipboard(currentGeneratedAnswerText, "Complete answer text copied to clipboard!");
});

// Particle System for Sunny, Rainy, Winter, Cloudy
function initThemeParticles() {
    const canvas = document.getElementById("theme-particles");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const maxParticles = 125;
    const particles = [];

    function getActiveWeather() {
        if (document.documentElement.classList.contains("weather-sunny")) return "sunny";
        if (document.documentElement.classList.contains("weather-rainy")) return "rainy";
        if (document.documentElement.classList.contains("weather-winter")) return "winter";
        if (document.documentElement.classList.contains("weather-cloudy")) return "cloudy";
        return "sunny";
    }

    for (let i = 0; i < maxParticles; i++) {
        particles.push(resetParticle({}, true));
    }

    function resetParticle(p, init = false) {
        const weather = getActiveWeather();
        p.weatherType = weather;
        p.x = Math.random() * width;

        if (weather === "sunny") {
            p.angle = Math.random() * Math.PI * 0.18 + Math.PI * 0.58;
            p.speed = Math.random() * 0.0006 + 0.0002;
            p.opacity = Math.random() * 0.12 + 0.04;
            p.width = Math.random() * 70 + 30;
            p.oscillationSpeed = Math.random() * 0.008 + 0.004;
            p.oscillationOffset = Math.random() * Math.PI * 2;
            // delete non-sunny keys
            delete p.y;
            delete p.radius;
        } else if (weather === "rainy") {
            p.y = init ? Math.random() * height : -50;
            p.length = Math.random() * 25 + 30; // Medium to larger rain streaks
            p.speed = Math.random() * 10 + 16; // Faster falling speed
            p.opacity = Math.random() * 0.28 + 0.12; // Natural crisp opacity
            p.angle = -0.06 - Math.random() * 0.04; // Sleek natural slant
            p.weight = Math.random() * 1.0 + 1.2; // Medium stroke width
            // delete non-rainy keys
            delete p.radius;
        } else if (weather === "winter") {
            p.y = init ? Math.random() * height : -20;
            p.radius = Math.random() * 2.8 + 0.8;
            p.speed = Math.random() * 1.2 + 0.4;
            p.opacity = Math.random() * 0.45 + 0.15;
            p.swingSpeed = Math.random() * 0.015 + 0.005;
            p.swingRange = Math.random() * 1.8 + 0.5;
            p.swingOffset = Math.random() * Math.PI * 2;
            // delete non-winter keys
            delete p.length;
        } else if (weather === "cloudy") {
            p.y = Math.random() * height * 0.9;
            p.radius = Math.random() * 150 + 80;
            p.x = init ? Math.random() * width : -p.radius * 2;
            p.speed = Math.random() * 0.25 + 0.08;
            p.opacity = Math.random() * 0.08 + 0.03;
            // delete non-cloudy keys
            delete p.length;
        }
        return p;
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        const weather = getActiveWeather();

        for (let i = 0; i < maxParticles; i++) {
            let p = particles[i];

            if (p.weatherType !== weather) {
                p = resetParticle(p, false);
            }

            // Limit particle densities depending on theme selection to prevent lag or crowding
            if (weather === "rainy") continue;
            if (weather === "sunny" && i >= 40) continue;
            if (weather === "cloudy" && i >= 15) continue;
            if (weather === "winter" && i >= 70) continue;

            if (weather === "sunny") {
                p.oscillationOffset += p.oscillationSpeed;
                let currentWidth = p.width + Math.sin(p.oscillationOffset) * 15;
                let opacity = p.opacity + Math.sin(p.oscillationOffset) * 0.02;

                let x1 = width - Math.cos(p.angle) * height - currentWidth / 2;
                let x2 = width - Math.cos(p.angle) * height + currentWidth / 2;

                let isLightMode = document.documentElement.classList.contains("light-mode");
                let beamColor = isLightMode ? `rgba(251, 191, 36, ${opacity * 0.2})` : `rgba(251, 191, 36, ${opacity * 0.1})`;

                ctx.beginPath();
                ctx.fillStyle = beamColor;
                ctx.moveTo(width, 0);
                ctx.lineTo(x1, height);
                ctx.lineTo(x2, height);
                ctx.closePath();
                ctx.fill();
            } else if (weather === "rainy") {
                p.y += p.speed;
                p.x += Math.sin(p.angle) * p.speed;

                ctx.beginPath();
                let isLightMode = document.documentElement.classList.contains("light-mode");
                ctx.strokeStyle = isLightMode ? `rgba(37, 99, 235, ${p.opacity})` : `rgba(96, 165, 250, ${p.opacity})`;
                ctx.lineWidth = p.weight;
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p.x + Math.sin(p.angle) * p.length, p.y + p.length);
                ctx.stroke();

                if (p.y > height || p.x < -20 || p.x > width + 20) {
                    resetParticle(p, false);
                }
            } else if (weather === "winter") {
                p.y += p.speed;
                p.swingOffset += p.swingSpeed;
                p.x += Math.sin(p.swingOffset) * p.swingRange * 0.5;

                ctx.beginPath();
                let isLightMode = document.documentElement.classList.contains("light-mode");
                ctx.fillStyle = isLightMode ? `rgba(71, 85, 105, ${p.opacity})` : `rgba(166, 200, 255, ${p.opacity})`;
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fill();

                if (p.y > height || p.x < -10 || p.x > width + 10) {
                    resetParticle(p, false);
                }
            } else if (weather === "cloudy") {
                p.x += p.speed;

                ctx.beginPath();
                let grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
                let isLightMode = document.documentElement.classList.contains("light-mode");
                let baseColor = isLightMode ? '148, 163, 184' : '100, 116, 139';
                grad.addColorStop(0, `rgba(${baseColor}, ${p.opacity})`);
                grad.addColorStop(1, `rgba(${baseColor}, 0)`);
                ctx.fillStyle = grad;
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fill();

                if (p.x - p.radius > width) {
                    resetParticle(p, false);
                }
            }
        }
        requestAnimationFrame(animate);
    }

    animate();
}

function getActiveWeatherName() {
    if (document.documentElement.classList.contains("weather-sunny")) return "sunny";
    if (document.documentElement.classList.contains("weather-rainy")) return "rainy";
    if (document.documentElement.classList.contains("weather-winter")) return "winter";
    if (document.documentElement.classList.contains("weather-cloudy")) return "cloudy";
    return "sunny";
}

function updateWeatherGraphic(activeWeather) {
    const idxBadge = document.getElementById("index-weather-badge");
    const qaBadge = document.getElementById("qa-weather-badge");
    
    if (idxBadge && qaBadge) {
        let idxContent = "";
        let qaContent = "";
        
        if (activeWeather === "sunny") {
            idxContent = `<i data-lucide="sun" class="animate-spin-slow" style="color: #fbbf24;"></i> <span>Sunny Theme</span>`;
            qaContent = `<i data-lucide="wind" style="color: #38bdf8;"></i> <span>Cooler Fan</span>`;
        } else if (activeWeather === "rainy") {
            idxContent = `<i data-lucide="umbrella" style="color: #60a5fa; animation: bounce 2s infinite;"></i> <span>Rainy Theme</span>`;
            qaContent = `<i data-lucide="cloud-rain" style="color: #60a5fa;"></i> <span>Umbrella Active</span>`;
        } else if (activeWeather === "winter") {
            idxContent = `<i data-lucide="snowflake" class="animate-pulse" style="color: #cbd5e1;"></i> <span>Winter Theme</span>`;
            qaContent = `<i data-lucide="snowflake" style="color: #93c5fd;"></i> <span>Snowballs Active</span>`;
        } else if (activeWeather === "cloudy") {
            idxContent = `<i data-lucide="cloud" style="color: #94a3b8;"></i> <span>Cloudy Theme</span>`;
            qaContent = `<i data-lucide="cloud-drizzle" style="color: #64748b;"></i> <span>Overcast Mist</span>`;
        }
        
        idxBadge.innerHTML = idxContent;
        qaBadge.innerHTML = qaContent;
    }
    
    // Re-trigger Lucide icon instantiation for newly injected icons
    if (window.lucide) {
        lucide.createIcons();
    }
}
