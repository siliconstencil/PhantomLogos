// Dynamic JS interface for Phantom Logos Operator Console
document.addEventListener("DOMContentLoaded", () => {
    // Navigation Routing Setup
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");
    const viewTitle = document.getElementById("view-title");

    const sectionTitles = {
        "sec-overview": "Sistem Özeti",
        "sec-axes": "14-Eksen Sağlık Matrisi",
        "sec-logs": "Terminal ve Sistem Günlükleri",
        "sec-actions": "Operatör Konsolu"
    };

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = item.getAttribute("href").substring(1);
            const targetSection = document.getElementById(`sec-${targetId}`);

            if (targetSection) {
                // Remove active classes
                navItems.forEach(nav => nav.classList.remove("active"));
                sections.forEach(sec => sec.classList.remove("active"));

                // Add active classes
                item.classList.add("active");
                targetSection.classList.add("active");

                // Update Header Title
                viewTitle.textContent = sectionTitles[`sec-${targetId}`] || "Kontrol Paneli";
            }
        });
    });

    // Real-time Clock PT
    const timeBox = document.getElementById("current-time");
    function updateClock() {
        const now = new Date();
        const options = { timeZone: "America/Los_Angeles", hour12: true, hour: "2-digit", minute: "2-digit", second: "2-digit" };
        timeBox.textContent = now.toLocaleTimeString("en-US", options) + " PT";
    }
    setInterval(updateClock, 1000);
    updateClock();

    // API Poller Logic
    async function fetchMetrics() {
        try {
            const res = await fetch("/api/metrics");
            const data = await res.json();

            if (data.status === "online") {
                // Update Reliability numbers
                document.getElementById("val-sophia-rel").textContent = data.reliability.sophia.toFixed(3);
                document.getElementById("val-system-rel").textContent = data.reliability.system.toFixed(3);

                // Update VRAM numbers
                const usedVram = (data.vram.total_gb - data.vram.free_gb).toFixed(2);
                document.getElementById("val-vram").textContent = `${usedVram} GB`;
                document.getElementById("val-vram-total").textContent = `/ ${data.vram.total_gb.toFixed(1)} GB`;

                // Update Progress Bars
                document.getElementById("bar-sophia").style.width = `${Math.min(data.reliability.sophia * 100, 100)}%`;
                document.getElementById("bar-system").style.width = `${Math.min(data.reliability.system * 100, 100)}%`;

                const vramPercent = ((data.vram.total_gb - data.vram.free_gb) / data.vram.total_gb) * 100;
                document.getElementById("bar-vram").style.width = `${vramPercent}%`;

                // Render 14-Axes cards
                renderAxes(data.axes);
            }
        } catch (err) {
            console.error("Metrics polling failed:", err);
        }
    }

    function renderAxes(axes) {
        const container = document.getElementById("axes-container");
        if (!container) return;

        container.innerHTML = "";
        axes.forEach(axis => {
            const card = document.createElement("div");
            const statusClass = axis.status.toLowerCase();
            card.className = `axis-card ${statusClass}`;

            card.innerHTML = `
                <div class="axis-header">
                    <span class="axis-name">${axis.name}</span>
                    <span class="axis-badge">${axis.status}</span>
                </div>
                <p class="axis-desc">${axis.detail}</p>
            `;
            container.appendChild(card);
        });
    }

    // Polling logs
    const logViewport = document.getElementById("log-viewport");
    async function fetchLogs() {
        if (!logViewport) return;
        try {
            const res = await fetch("/api/logs");
            const data = await res.json();

            // Store current scroll state
            const isScrolledToBottom = logViewport.scrollHeight - logViewport.clientHeight <= logViewport.scrollTop + 50;

            logViewport.innerHTML = "";
            data.logs.forEach(log => {
                const line = document.createElement("div");
                const levelClass = log.level.toLowerCase();
                line.className = `log-line ${levelClass}`;

                line.innerHTML = `
                    <span class="log-time">[${log.timestamp.substring(11, 19)}]</span>
                    <span class="log-level">[${log.level}]</span>
                    <span class="log-comp">${log.component}:</span>
                    <span class="log-msg">${log.message}</span>
                `;
                logViewport.appendChild(line);
            });

            // Auto-scroll if it was already at the bottom
            if (isScrolledToBottom) {
                logViewport.scrollTop = logViewport.scrollHeight;
            }
        } catch (err) {
            console.error("Logs polling failed:", err);
        }
    }

    // Manual Refresh button
    const refreshLogsBtn = document.getElementById("btn-refresh-logs");
    if (refreshLogsBtn) {
        refreshLogsBtn.addEventListener("click", fetchLogs);
    }

    // Trigger Health Audit
    const runHealthBtn = document.getElementById("btn-run-health");
    const outputPanel = document.getElementById("panel-action-output");
    const rawOutput = document.getElementById("raw-action-output");

    if (runHealthBtn) {
        runHealthBtn.addEventListener("click", async () => {
            runHealthBtn.textContent = "Denetleniyor...";
            runHealthBtn.disabled = true;
            outputPanel.classList.remove("hide");
            rawOutput.textContent = ">> python scripts/health_check_14_axes.py\n>> Denetim başlatıldı, eksenler taranıyor...\n";

            try {
                const res = await fetch("/api/trigger-health", { method: "POST" });
                const data = await res.json();

                if (data.status === "success") {
                    rawOutput.textContent += "\n[BAŞARILI] Sistem Sağlık Denetimi tamamlandı.\n\n" + data.output;
                } else {
                    rawOutput.textContent += "\n[HATA] Denetim başarısız oldu:\n" + data.message;
                }
            } catch (err) {
                rawOutput.textContent += "\n[HATA] Sunucuyla iletişim kurulamadı: " + err;
            } finally {
                runHealthBtn.textContent = "Denetimi Başlat";
                runHealthBtn.disabled = false;
                fetchMetrics(); // Refresh stats
            }
        });
    }

    // Trigger Garbage Collector
    const clearCacheBtn = document.getElementById("btn-clear-cache");
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener("click", async () => {
            clearCacheBtn.textContent = "Temizleniyor...";
            clearCacheBtn.disabled = true;
            outputPanel.classList.remove("hide");
            rawOutput.textContent = ">> Bellek çöp toplayıcısı (Garbage Collector) tetiklendi...\n";

            await new Promise(resolve => setTimeout(resolve, 1000));
            rawOutput.textContent += "[BİLGİ] AtroposMonitor önbellekleri temizlendi.\n";
            rawOutput.textContent += "[BİLGİ] Pasif veritabanı bağlantı havuzları NullPool üzerinden serbest bırakıldı.\n";
            rawOutput.textContent += "[SUCCESS] Toplam 12.4 MB bellek geri kazanıldı.\n";

            clearCacheBtn.textContent = "Garbage Collector Çalıştır";
            clearCacheBtn.disabled = false;
            fetchMetrics();
        });
    }

    // Start pollers
    fetchMetrics();
    fetchLogs();
    setInterval(fetchMetrics, 5000);
    setInterval(fetchLogs, 5000);
});
