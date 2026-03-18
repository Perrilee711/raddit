(() => {
  const body = document.body;
  const buttons = Array.from(document.querySelectorAll("[data-lang]"));
  const storageKey = "fishgoo-site-lang";
  let storage = null;

  try {
    storage = window.localStorage;
  } catch (error) {
    storage = null;
  }

  const applyLang = (lang) => {
    const next = lang === "en" ? "en" : "zh";
    body.classList.remove("lang-zh", "lang-en");
    body.classList.add(`lang-${next}`);
    document.documentElement.lang = next === "zh" ? "zh-CN" : "en";
    if (storage) {
      storage.setItem(storageKey, next);
    }
  };

  const initial = storage ? storage.getItem(storageKey) || "zh" : "zh";
  applyLang(initial);

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      applyLang(button.dataset.lang);
    });
  });
})();
