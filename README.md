# Система верификации сотрудников

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-ComputerVision-ff6b35?style=flat&logo=yolo)](https://github.com/ultralytics/ultralytics)
[![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-3c79f5?style=flat&logo=qdrant)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)

---

## О проекте

**Двухэтапная система верификации** сотрудников: распознавание лица + OCR бейджа.  
Детектирует СИЗ, проверяет наличие одного человека в кадре, распознаёт лицо через, считывает бейдж через, сверяет личность.

Production-ready: асинхронный WebSocket стрим, потокобезопасная обработка, детекция движения, полная обработка ошибка.

---

## Производительность и оптимизация

Система прошла ряд оптимизаций для обеспечения работы в реальном времени:

| Метрика | Значение | Комментарий |
|---------|----------|-------------|
| **FPS (обработка)** | **12–14 FPS** | При активной детекции и верификации |
| **FPS (idle)** | **~22 FPS** | Когда YOLO не детектирует объекты (оптимизация) |
| **WebSocket стрим** | **6 → 14 FPS** | Оптимизация передачи кадров и сжатия |
| **Heavy Frame (OCR+InsightFace)** | **600ms → 60ms** | Вынос тяжелых операций в отдельные потоки |

### Примененные техники оптимизации:
- **YOLOv8 Inference**: Запуск детекции не каждый кадр, а раз в 1.5с или при изменении сцены.
- **Multithreading**: Параллельная обработка OCR и векторизации лица (InsightFace) для тяжелых кадров.
- **WebSocket Compression**: Сжатие JPEG (quality=75%) и оптимизация буферизации.
- **Motion Detection**: Обработка только при наличии движения (IoU > 0.9, стабильность 30 кадров).
- **Thread-safe queues**: Безопасный обмен данными между потоками без блокировок.

---

## Технологии

- **YOLOv8** — детекция лиц, бейджей, СИЗ (кепка, маска, очки)
- **InsightFace + Qdrant** — распознавание лиц с векторной БД
- **Tesseract OCR** — чтение ФИО с бейджей
- **FastAPI + WebSockets** — стриминг видео в реальном времени
- **FSM** — UNREGISTERED → VECTORIZED → OCR → VERIFY/ERROR
- **Детекция движения** — обработка только стабильных объектов
- **Thread-safe** — безопасный обмен данными между потоками

---

## Как запустить

### 1. Установка
```bash
pip install -r requirements.txt
```

### 2. Настройка `.env`
Скопируй `.env.example` в `.env` и настрой:
```env
MODEL_PATH=/path/to/your/yolo/best.pt
IDEAL_PATH=/path/to/ideal_faces/
PRODUCER_URL=ws://localhost:8080/ws/video
```

### 3. Запуск producer (камера)
```bash
# В директории producer
uvicorn producer:app --host 0.0.0.0 --port 8080
```

### 4. Запуск верификатора
```bash
uvicorn app.backend:app --host 0.0.0.0 --port 8081
```

### 5. Стрим в браузере
Открой файл `frontend/index.html`

**Алгоритм**: Стань в кадр → Сними СИЗ → Скан лица → Покажи бейдж → SUCCESS/ERROR

---

## Архитектура

```
Видеопоток (WebSocket)
         ↓
Raw Queue → YOLO (каждые 1.5с) → Pipeline FSM
                       ↓
        Потоки: Face Vec → Qdrant ← OCR Бейдж
                       ↓
                Identity Match
                       ↓
                Обработанный стрим
```

---

## Логика работы

| Этап | Проверка | Действие |
|------|----------|----------|
| **1. Регистрация** | 1 человек, без СИЗ | Векторизация лица → поиск в Qdrant |
| **2. Скан бейджа** | Стабильный бейдж (30 кадров) | OCR → извлечение текста |
| **3. Верификация** | Схожесть имён > 0.7 | SUCCESS/ERROR + сброс |

---

## Структура проекта

```
app/
├── backend.py         # FastAPI + WebSocket
├── pipeline.py        # Основная логика FSM
├── model_detection.py # Обёртка YOLOv8
├── qdrant.py          # Распознавание лиц и векторная БД
├── person.py          # Машина состояний личности (FSM)
├── ocr.py             # OCR бейджей
├── utils.py           # IoU, детекция движения
└── config.py          # Настройки и пороги
```

---

## Планы развития (Roadmap)

### Инфраструктура и DevOps
- [ ] **Контейнеризация**: Полная миграция на Docker Compose (изолированные сервисы, volumes, networks).
- [ ] **CI/CD**: Настройка GitHub Actions / GitLab CI для автотестов и деплоя.
- [ ] **Мониторинг**: Интеграция Prometheus + Grafana + Loki для метрик и логирования.
- [ ] **Тестирование**: Покрытие unit- и integration-тестами (pytest), нагрузочное тестирование WebSocket.

### Производительность и ML
- [ ] **C++ Backend**: Перенос CPU-bound операций (предобработка, OCR, инференс) в C++ модули (pybind11/ctypes).
- [ ] **ONNX Runtime**: Конвертация и тестирование моделей YOLO/InsightFace в ONNX для ускорения инференса.
- [ ] **Generative Data**: Генерация синтетических данных (аугментация) для улучшения качества обучения моделей.

### Данные и Frontend
- [ ] **Frontend Rewrite**: Разработка полноценного UI (React/Vue) с дашбордом, логами и настройками.
- [ ] **Database Migration**: Переход от файлов/JSON к полноценной БД (PostgreSQL) для хранения пользователей и логов.
- [ ] **Workers Config**: Вынос конфигурации работников в JSON/YAML для гибкого управления без перезапуска.

---

*Автор [Wkdk00](https://github.com/Wkdk00) — Февраль 2026*