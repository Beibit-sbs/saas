# I18N Checklist (kk/ru/en)

Use this checklist in every project.

## Coverage
- [ ] All user-facing pages have translations
- [ ] Form labels/placeholders/errors are translated
- [ ] Navigation and dashboard sections are translated
- [ ] In-app help assistant supports kk/ru/en

## Technical
- [ ] Language switcher is visible in UI
- [ ] Language is persisted (localStorage or profile)
- [ ] Fallback language is defined (ru by default)
- [ ] API responses with user text support language context
- [ ] Shared components (header, sidebar, profile, session panel, help, dialogs) react to language changes
- [ ] Language change propagates to the whole active screen, not only to the selector widget

## QA
- [ ] Smoke test each flow in kk
- [ ] Smoke test each flow in ru
- [ ] Smoke test each flow in en
- [ ] No mixed-language UI fragments in one screen
- [ ] Profile page changes language together with the rest of the UI
- [ ] Login and landing pages also reflect the selected language
