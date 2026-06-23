(function () {
  const screen = document.querySelector(".screen[data-reaction]");
  if (!screen) return;

  const reaction = screen.getAttribute("data-reaction");
  if (!reaction) return;

  // Let the reaction animation play, then fall back to the idle state.
  setTimeout(() => {
    screen.setAttribute("data-reaction", "");
  }, 1800);

  // Strip ?reacted=... from the address bar so refreshing doesn't replay it.
  if (window.history && window.history.replaceState) {
    const url = new URL(window.location.href);
    url.searchParams.delete("reacted");
    window.history.replaceState({}, "", url);
  }
})();
