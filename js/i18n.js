const SUPPORTED_LANGUAGES = ["en", "de", "ru"];
const DEFAULT_LANGUAGE = "en";

function getLanguageFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const lang = params.get("lang");

  if (SUPPORTED_LANGUAGES.includes(lang)) {
    return lang;
  }

  return null;
}

function getSavedLanguage() {
  const saved = localStorage.getItem("ddf_language");

  if (SUPPORTED_LANGUAGES.includes(saved)) {
    return saved;
  }

  return null;
}

function getCurrentLanguage() {
  return (
    getLanguageFromUrl() ||
    getSavedLanguage() ||
    DEFAULT_LANGUAGE
  );
}

async function loadTranslations(language) {
  const response = await fetch(`/data/i18n/${language}.json`);

  if (!response.ok) {
    throw new Error(
      `Could not load translations for language: ${language}`
    );
  }

  return response.json();
}

function getNestedValue(object, path) {
  return path.split(".").reduce((value, key) => {
    if (value && Object.prototype.hasOwnProperty.call(value, key)) {
      return value[key];
    }

    return null;
  }, object);
}

function applyTranslations(translations) {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    const translatedValue = getNestedValue(translations, key);

    if (typeof translatedValue === "string") {
      element.textContent = translatedValue;
    }
  });
}

function updateLanguageLinks(language) {
  document.querySelectorAll("[data-language]").forEach((link) => {
    const linkLanguage = link.dataset.language;

    link.classList.toggle(
      "active",
      linkLanguage === language
    );
  });
}

async function initializeI18n() {
  const language = getCurrentLanguage();

  try {
    const translations = await loadTranslations(language);

    applyTranslations(translations);
    updateLanguageLinks(language);

    localStorage.setItem("ddf_language", language);
    document.documentElement.lang = language;
  } catch (error) {
    console.error("Translation initialization failed:", error);
  }
}

document.addEventListener("DOMContentLoaded", initializeI18n);
