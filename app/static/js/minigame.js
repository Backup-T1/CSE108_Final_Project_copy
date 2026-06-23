(function () {
  const box = document.getElementById("minigame-box");
  const target = document.getElementById("minigame-target");
  const result = document.getElementById("minigame-result");
  const info = document.getElementById("minigame-info");
  const playsUsedEl = document.getElementById("minigame-plays-used");
  if (!box || !target) return;

  let moveTimer = null;

  function moveTarget() {
    const maxX = box.clientWidth - target.clientWidth - 10;
    const maxY = box.clientHeight - target.clientHeight - 10;
    target.style.left = Math.max(0, Math.random() * maxX) + "px";
    target.style.top = Math.max(0, Math.random() * maxY) + "px";
  }

  // The target dodges every 900ms so players have to react quickly.
  function startDodging() {
    moveTarget();
    moveTimer = setInterval(moveTarget, 900);
  }

  function showExhausted(maxPlays) {
    clearInterval(moveTimer);
    if (info) {
      info.textContent = `No plays left today (${maxPlays} of ${maxPlays} used). Come back tomorrow for more coins.`;
    }
    box.style.display = "none";
    result.textContent = "";
  }

  startDodging();

  target.addEventListener("click", async () => {
    clearInterval(moveTimer);
    target.disabled = true;

    try {
      const res = await fetch("/shop/minigame/play", { method: "POST" });
      const data = await res.json();

      // Always reflect the real plays-used count from the server, on every
      // click, win or not, so the text on screen never goes stale.
      if (playsUsedEl && typeof data.plays_used === "number") {
        playsUsedEl.textContent = data.plays_used;
      }

      if (data.ok) {
        result.textContent = `Nice! +${data.payout} coins.`;
        const coinPill = document.querySelector(".coin-pill");
        if (coinPill) coinPill.textContent = `${data.coins} Coins`;

        if (data.plays_used >= data.max_plays) {
          showExhausted(data.max_plays);
          return;
        }
      } else {
        showExhausted(data.max_plays);
        return;
      }
    } catch (err) {
      result.textContent = "Something went wrong - try again.";
    }

    setTimeout(() => {
      target.disabled = false;
      startDodging();
    }, 1200);
  });
})();
