#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль симуляции Солнечной системы v3.0
=======================================
Интерактивная 3D-визуализация (в 2D-проекции) движения планет вокруг Солнца.

Основные возможности:
- Реалистичное движение планет по эллиптическим орбитам (упрощенная модель Кеплера)
- Интерактивное управление масштабом (зум) и скоростью анимации
- Режимы отображения: орбиты, названия, следы движения
- Информационная панель с подробными данными о каждом небесном теле
- Возможность слежения камерой за выбранной планетой

Физическая модель:
- Орбиты представлены как окружности (упрощение, эксцентриситет не учитывается)
- Для визуального сжатия орбит по вертикали применяется коэффициент 0.4
- Время симуляции масштабируется для наглядности (1 год за несколько секунд)
"""

import tkinter as tk
from tkinter import ttk
import math
import time
from PIL import Image, ImageTk
import os
from typing import Dict, List, Optional, Tuple, Any


class SolarSystemSimulation:
    """
    Главный класс симуляции Солнечной системы.
    
    Отвечает за:
    - Инициализацию графического интерфейса
    - Управление параметрами симуляции (скорость, масштаб, режимы)
    - Расчет позиций планет на основе времени
    - Отрисовку всех элементов на холсте
    - Обработку пользовательского ввода
    
    Атрибуты:
        root (tk.Tk): Главное окно приложения
        time_scale (float): Множитель скорости симуляции (1.0 = реальная скорость)
        zoom (float): Текущий масштаб отображения
        target_zoom (float): Целевой масштаб для плавной анимации
        running (bool): Флаг работы основного цикла
        planets_data (dict): Словарь с данными всех планет
    """
    
    def __init__(self, root: tk.Tk):
        """
        Инициализация симуляции.
        
        Args:
            root: Главное окно Tkinter, в котором будет размещена симуляция
            
        Примечание:
            Все физические параметры (размеры, расстояния) масштабированы
            для удобства визуализации, а не для физической точности.
        """
        self.root = root
        self.root.title("Симуляция Солнечной системы v3.0")
        self.root.geometry("1400x800")
        self.root.configure(bg="#0a0a2a")  # Тёмно-синий фон, имитирующий космос
        
        # Параметры симуляции
        self.time_scale = 0.5                # Начальная скорость (0.5 от реальной)
        self.zoom = 1.0                       # Текущий масштаб
        self.target_zoom = 1.0                 # Целевой зум для плавности
        self.running = True                    # Флаг работы программы
        self.start_time = time.time()           # Время запуска для расчета симуляции
        self.planet_angles: Dict[str, float] = {}  # Текущие углы планет (для следов)
        self.show_orbits = True                  # Отображение орбит
        self.show_names = True                   # Отображение названий
        self.trail_mode = False                   # Режим отображения следов
        self.planet_trails: Dict[str, List[Tuple[float, float]]] = {}  # Следы планет
        self.selected_planet: Optional[str] = None  # Выбранная планета
        self.follow_mode = False                    # Режим слежения за планетой
        self.paused = False                         # Пауза симуляции
        self.pause_time = 0                          # Время при паузе
        
        # Константы масштабирования
        # Астрономическая единица в пикселях (1 AU = расстояние Земля-Солнце)
        self.AU = 120
        
        # Радиус Земли в пикселях при масштабе 1.0
        self.EARTH_RADIUS = 8
        
        # Солнце уменьшено для лучшего обзора (в реальности в 109 раз больше Земли)
        # ИЗМЕНЕНО: уменьшили Солнце с 20 до 12 раз больше Земли
        self.SUN_RADIUS = self.EARTH_RADIUS * 12  # Было 20, стало 12
        
        # Базовое замедление орбитальных периодов для наглядности анимации
        # Реальные периоды слишком велики для интерактивной визуализации
        self.BASE_SLOWDOWN = 20
        
        # Цвета для планет (используются, если нет изображений)
        self.planet_colors = {
            'Меркурий': '#c0c0c0',  # Серебристый
            'Венера': '#ffd700',     # Золотистый
            'Земля': '#4169e1',       # Королевский синий
            'Марс': '#ff4500',        # Оранжево-красный
            'Юпитер': '#d2b48c',      # Светло-коричневый
            'Сатурн': '#f4a460',      # Песочный
            'Уран': '#7fffd4',        # Бирюзовый
            'Нептун': '#1e90ff'       # Ярко-синий
        }
        
        # Данные планет
        # Все значения масштабированы для визуализации, кроме текстовых описаний
        self.planets_data = {
            'Меркурий': {
                'distance': 0.4,        # Расстояние от Солнца в AU
                'size_ratio': 0.38,      # Размер относительно Земли
                'color': '#c0c0c0',       # Цвет для отрисовки
                'orbit_period': 0.24 * self.BASE_SLOWDOWN,  # Период обращения (симуляция)
                'rotation_period': 58.6,  # Период вращения (реальные сутки)
                # Далее следуют реальные физические характеристики для информационной панели
                'mass': '3.30×10²³ кг', 
                'diameter': '4,879 км',
                'density': '5.43 г/см³', 
                'temperature': '-173°C до 427°C',
                'gravity': '3.7 м/с²', 
                'moons': 0, 
                'atmosphere': 'Очень разреженная',
                'discovery': 'Известна с древних времен', 
                'type': 'Планета земной группы',
                'description': 'Самая близкая к Солнцу планета. Днем поверхность нагревается до 427°C, а ночью остывает до -173°C.'
            },
            'Венера': {
                'distance': 0.7, 'size_ratio': 0.95, 'color': '#ffd700',
                'orbit_period': 0.62 * self.BASE_SLOWDOWN,
                'rotation_period': 243,
                'mass': '4.87×10²⁴ кг', 'diameter': '12,104 км',
                'density': '5.24 г/см³', 'temperature': '462°C',
                'gravity': '8.87 м/с²', 'moons': 0, 'atmosphere': 'Углекислый газ (96%)',
                'discovery': 'Известна с древних времен', 'type': 'Планета земной группы',
                'description': 'Вращается в противоположную сторону. Самая горячая планета.'
            },
            'Земля': {
                'distance': 1.0, 'size_ratio': 1.0, 'color': '#4169e1',
                'orbit_period': 1.0 * self.BASE_SLOWDOWN,
                'rotation_period': 1.0,
                'mass': '5.97×10²⁴ кг', 'diameter': '12,742 км',
                'density': '5.51 г/см³', 'temperature': '-88°C до 58°C',
                'gravity': '9.8 м/с²', 'moons': 1, 'atmosphere': 'Азот (78%), кислород (21%)',
                'discovery': 'Наш дом', 'type': 'Планета земной группы',
                'description': 'Единственная известная планета с жизнью. 71% поверхности покрыто водой.'
            },
            'Марс': {
                'distance': 1.5, 'size_ratio': 0.53, 'color': '#ff4500',
                'orbit_period': 1.88 * self.BASE_SLOWDOWN,
                'rotation_period': 1.03,
                'mass': '6.42×10²³ кг', 'diameter': '6,779 км',
                'density': '3.93 г/см³', 'temperature': '-63°C',
                'gravity': '3.71 м/с²', 'moons': 2, 'atmosphere': 'Углекислый газ (95%)',
                'discovery': 'Известна с древних времен', 'type': 'Планета земной группы',
                'description': 'Имеет самую высокую гору - Олимп (22 км).'
            },
            'Юпитер': {
                'distance': 5.2, 'size_ratio': 11.2, 'color': '#d2b48c',
                'orbit_period': 11.86 * self.BASE_SLOWDOWN,
                'rotation_period': 0.41,
                'mass': '1.90×10²⁷ кг', 'diameter': '139,820 км',
                'density': '1.33 г/см³', 'temperature': '-108°C',
                'gravity': '24.79 м/с²', 'moons': 79, 'atmosphere': 'Водород (90%), гелий (10%)',
                'discovery': 'Известна с древних времен', 'type': 'Газовый гигант',
                'description': 'Самая большая планета. Имеет Большое красное пятно.'
            },
            'Сатурн': {
                'distance': 9.5, 'size_ratio': 9.5, 'color': '#f4a460',
                'orbit_period': 29.46 * self.BASE_SLOWDOWN,
                'rotation_period': 0.45,
                'mass': '5.68×10²⁶ кг', 'diameter': '116,460 км',
                'density': '0.69 г/см³', 'temperature': '-139°C',
                'gravity': '10.44 м/с²', 'moons': 82, 'atmosphere': 'Водород (96%), гелий (3%)',
                'discovery': 'Известна с древних времен', 'type': 'Газовый гигант',
                'description': 'Имеет красивые кольца из льда и пыли. Мог бы плавать в воде.'
            },
            'Уран': {
                'distance': 19.0, 'size_ratio': 4.0, 'color': '#7fffd4',
                'orbit_period': 84.01 * self.BASE_SLOWDOWN,
                'rotation_period': 0.72,
                'mass': '8.68×10²⁵ кг', 'diameter': '50,724 км',
                'density': '1.27 г/см³', 'temperature': '-197°C',
                'gravity': '8.69 м/с²', 'moons': 27, 'atmosphere': 'Водород, гелий, метан',
                'discovery': 'Уильям Гершель, 1781', 'type': 'Ледяной гигант',
                'description': 'Вращается "на боку", ось наклонена на 98 градусов.'
            },
            'Нептун': {
                'distance': 30.0, 'size_ratio': 3.9, 'color': '#1e90ff',
                'orbit_period': 164.8 * self.BASE_SLOWDOWN,
                'rotation_period': 0.67,
                'mass': '1.02×10²⁶ кг', 'diameter': '49,244 км',
                'density': '1.64 г/см³', 'temperature': '-201°C',
                'gravity': '11.15 м/с²', 'moons': 14, 'atmosphere': 'Водород, гелий, метан',
                'discovery': 'Иоганн Галле, 1846', 'type': 'Ледяной гигант',
                'description': 'Самые сильные ветра в Солнечной системе (до 2100 км/ч).'
            }
        }
        
        # Словарь для хранения изображений для информационной панели
        self.info_images: Dict[str, Optional[ImageTk.PhotoImage]] = {}
        
        self.create_widgets()
        self.load_images()
        
        # Привязываем события мыши для интерактивного управления
        self.canvas.bind("<Button-3>", self.on_right_click)  # Правая кнопка - начало зума
        self.canvas.bind("<B3-Motion>", self.on_right_drag)  # Движение с правой кнопкой - изменение зума
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Колесико мыши - изменение зума
        
        # Запускаем основной цикл обновления
        self.update()
    
    def on_right_click(self, event: tk.Event) -> None:
        """
        Обработчик нажатия правой кнопки мыши.
        
        Args:
            event: Событие Tkinter, содержащее координаты клика
            
        Сохраняет начальную позицию для расчета изменения зума при перетаскивании.
        """
        self.drag_start_y = event.y
        self.initial_zoom = self.zoom
    
    def on_right_drag(self, event: tk.Event) -> None:
        """
        Обработчик перетаскивания с зажатой правой кнопкой.
        
        Args:
            event: Событие Tkinter с текущими координатами мыши
            
        Реализует изменение масштаба вертикальным движением мыши:
        - Вверх (уменьшение Y) -> увеличение масштаба
        - Вниз (увеличение Y) -> уменьшение масштаба
        """
        if hasattr(self, 'drag_start_y'):
            # Вычисляем изменение зума пропорционально перемещению мыши
            delta = (self.drag_start_y - event.y) / 200
            new_zoom = self.initial_zoom + delta * self.initial_zoom
            
            # ИЗМЕНЕНО: увеличили максимальное отдаление с 0.2 до 0.1
            # Ограничиваем зум разумными пределами (10% - 500%)
            new_zoom = max(0.1, min(5.0, new_zoom))  # Было 0.2, стало 0.1
            
            # Устанавливаем новый зум
            self.target_zoom = new_zoom
            self.zoom = new_zoom
            self.zoom_scale.set(new_zoom)
            self.update_zoom_display()
            
            # Перезагружаем изображения с новым масштабом
            self.load_images()
    
    def on_mousewheel(self, event: tk.Event) -> None:
        """
        Обработчик колесика мыши.
        
        Args:
            event: Событие Tkinter, содержащее направление вращения колесика
                  (event.delta > 0 - вверх, < 0 - вниз)
                  
        Изменяет масштаб на 10% за шаг колесика.
        """
        # Определяем направление колесика
        if event.delta > 0:
            self.target_zoom *= 1.1  # Увеличиваем на 10%
        else:
            self.target_zoom *= 0.9  # Уменьшаем на 10%
        
        # ИЗМЕНЕНО: увеличили максимальное отдаление с 0.2 до 0.1
        # Ограничиваем зум
        self.target_zoom = max(0.1, min(5.0, self.target_zoom))  # Было 0.2, стало 0.1
        self.zoom = self.target_zoom
        self.zoom_scale.set(self.target_zoom)
        self.update_zoom_display()
        
        # Перезагружаем изображения
        self.load_images()
    
    def update_zoom_display(self) -> None:
        """
        Обновляет отображение текущего масштаба в интерфейсе.
        
        Меняет цвет индикатора в зависимости от величины масштаба:
        - Синий: дальний обзор (<50%)
        - Зеленый: нормальный (50-100%)
        - Фиолетовый: средний (100-150%)
        - Оранжевый: крупный (150-200%)
        - Красный: очень крупный (>200%)
        """
        percent = int(self.zoom * 100)
        self.zoom_label.config(text=f"{percent}%")
        self.zoom_value_label.config(text=f"{percent}%")
        
        # Меняем цвет в зависимости от масштаба
        if self.zoom < 0.5:
            color = "#4444aa"  # Синий - дальний обзор
        elif self.zoom < 1.0:
            color = "#44aa44"  # Зеленый - нормальный
        elif self.zoom < 1.5:
            color = "#aa44aa"  # Фиолетовый - средний
        elif self.zoom < 2.0:
            color = "#ffaa00"  # Оранжевый - крупный
        else:
            color = "#ff4444"  # Красный - очень крупный
        
        self.zoom_label.config(fg=color)
        self.zoom_value_label.config(fg=color)
    
    def load_images(self) -> None:
        """
        Загружает и масштабирует изображения планет.
        
        Особенности:
        - Изображения масштабируются под текущий zoom
        - При отсутствии файла используется отрисовка кругами
        - Создаются две версии: для холста и для информационной панели
        
        Пути к файлам указаны относительно корня проекта.
        В случае ошибки загрузки изображение заменяется на None.
        """
        self.planet_images = {}
        image_files = {
            'Солнце': 'фото/photo_2026-02-26_09-07-44-Photoroom.png',
            'Меркурий': 'фото/photo_2026-02-26_09-07-57-Photoroom.png',
            'Венера': 'фото/photo_2026-02-26_12-31-40-Photoroom (2).png',
            'Земля': 'фото/photo_2026-02-26_12-35-04-Photoroom.png',
            'Марс': 'фото/photo_2026-02-26_12-36-39-Photoroom.png',
            'Юпитер': 'фото/photo_2026-02-26_12-37-26-Photoroom.png',
            'Сатурн': 'фото/photo_2026-02-26_12-39-23-Photoroom.png',
            'Уран': 'фото/photo_2026-02-26_12-39-23-Photoroom.png',
            'Нептун': 'фото/photo_2026-02-26_09-09-47-Photoroom.png'
        }
        
        for planet_name, filename in image_files.items():
            try:
                if os.path.exists(filename):
                    img = Image.open(filename)
                    if planet_name == 'Солнце':
                        # ИЗМЕНЕНО: Солнце теперь еще меньше (с учетом нового SUN_RADIUS)
                        size = int(self.SUN_RADIUS * 2 * self.zoom)
                    else:
                        size_ratio = self.planets_data.get(planet_name, {}).get('size_ratio', 1.0)
                        size = int(self.EARTH_RADIUS * 2 * size_ratio * self.zoom)
                    
                    # Сохраняем пропорции при масштабировании
                    img.thumbnail((size, size), Image.Resampling.LANCZOS)
                    self.planet_images[planet_name] = ImageTk.PhotoImage(img)
                    
                    # Также загружаем версию для информационной панели (фиксированный размер)
                    info_img = Image.open(filename)
                    info_img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    self.info_images[planet_name] = ImageTk.PhotoImage(info_img)
                else:
                    print(f"Файл не найден: {filename}")
                    self.planet_images[planet_name] = None
                    self.info_images[planet_name] = None
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")
                self.planet_images[planet_name] = None
                self.info_images[planet_name] = None
    
    def create_widgets(self) -> None:
        """Создание всех элементов графического интерфейса."""
        # Верхняя панель с заголовком
        title_frame = tk.Frame(self.root, bg="#1a1a3a", height=50)
        title_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(title_frame, text="🌍 СИМУЛЯЦИЯ СОЛНЕЧНОЙ СИСТЕМЫ 🌞", 
                bg="#1a1a3a", fg="white", font=("Arial", 18, "bold")).pack(pady=10)
        
        # Основной холст для отрисовки
        canvas_frame = tk.Frame(self.root, bg="#0a0a2a")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#0a0a2a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Информационная панель справа
        self.create_info_panel()
        
        # Панель управления снизу
        self.create_control_panel()
        
        # Левая панель с кнопками планет
        self.create_left_panel()
        
        self.show_welcome_info()
    
    def create_info_panel(self) -> None:
        """
        Создание правой информационной панели.
        
        Панель содержит:
        - Текущее время симуляции
        - Фото выбранного объекта
        - Подробную текстовую информацию
        - Полосу прокрутки для длинных описаний
        """
        self.info_frame = tk.Frame(self.root, bg="#1a1a3a", width=400)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.info_frame.pack_propagate(False)
        
        # Заголовок с текущим временем
        tk.Label(self.info_frame, text="⏱ ВРЕМЯ СИМУЛЯЦИИ", 
                bg="#1a1a3a", fg="white", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.sim_time_label = tk.Label(self.info_frame, text="0 лет", 
                                      bg="#1a1a3a", fg="#00ff00", font=("Arial", 14, "bold"))
        self.sim_time_label.pack(pady=5)
        
        # Разделитель
        ttk.Separator(self.info_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Информация об объекте
        tk.Label(self.info_frame, text="ℹ ИНФОРМАЦИЯ ОБ ОБЪЕКТЕ", 
                bg="#1a1a3a", fg="white", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Фрейм для фото планеты
        self.photo_frame = tk.Frame(self.info_frame, bg="#2a2a4a", height=120)
        self.photo_frame.pack(fill=tk.X, padx=5, pady=5)
        self.photo_frame.pack_propagate(False)
        
        self.photo_label = tk.Label(self.photo_frame, bg="#2a2a4a")
        self.photo_label.pack(expand=True)
        
        # Текстовое поле с прокруткой
        text_frame = tk.Frame(self.info_frame, bg="#2a2a4a")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = tk.Text(text_frame, bg="#2a2a4a", fg="white", 
                                 font=("Arial", 10), wrap=tk.WORD,
                                 relief=tk.FLAT, borderwidth=0)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
    
    def create_control_panel(self) -> None:
        """
        Создание нижней панели управления.
        
        Содержит три ряда элементов:
        1. Ползунки скорости и масштаба с пресетами
        2. Кнопки управления режимами
        3. Подсказки по использованию
        
        Все элементы сгруппированы по функциональности и имеют всплывающие подсказки.
        """
        control_frame = tk.Frame(self.root, bg="#1a1a3a", height=200)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        control_frame.pack_propagate(False)
        
        # Верхний ряд - основные ползунки
        top_row = tk.Frame(control_frame, bg="#1a1a3a")
        top_row.pack(fill=tk.X, pady=10)
        
        # ========== СКОРОСТЬ ==========
        speed_frame = tk.Frame(top_row, bg="#1a1a3a", relief=tk.RAISED, borderwidth=2)
        speed_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(speed_frame, text="⚡ СКОРОСТЬ", bg="#1a1a3a", fg="#ffaa00", 
                font=("Arial", 11, "bold")).pack()
        
        tk.Label(speed_frame, text="(медленнее ← → быстрее)", bg="#1a1a3a", fg="#888888", 
                font=("Arial", 8)).pack()
        
        speed_control = tk.Frame(speed_frame, bg="#1a1a3a")
        speed_control.pack(pady=5)
        
        self.speed_scale = ttk.Scale(speed_control, from_=0.1, to=500, 
                                     orient=tk.HORIZONTAL, length=200,
                                     command=self.change_speed)
        self.speed_scale.set(0.5)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = tk.Label(speed_control, text="0.5x", bg="#1a1a3a", 
                                   fg="#00ff00", font=("Arial", 12, "bold"))
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопки предустановленной скорости
        speed_buttons = tk.Frame(speed_frame, bg="#1a1a3a")
        speed_buttons.pack(pady=5)
        
        speed_presets = [
            ("0.1x", 0.1, "#ff4444", "Очень медленно"),
            ("0.5x", 0.5, "#ff8844", "Медленно"),
            ("1x", 1, "#44ff44", "Нормально"),
            ("5x", 5, "#4444ff", "Быстро"),
            ("10x", 10, "#aa44ff", "Очень быстро")
        ]
        
        for text, val, color, tip in speed_presets:
            btn = tk.Button(speed_buttons, text=text, width=5, bg=color, fg="white",
                          font=("Arial", 9, "bold"), command=lambda v=val: self.set_speed(v))
            btn.pack(side=tk.LEFT, padx=2)
            self.create_tooltip(btn, tip)
        
        # ========== МАСШТАБ (ЗУМ) ==========
        zoom_frame = tk.Frame(top_row, bg="#1a1a3a", relief=tk.RAISED, borderwidth=2)
        zoom_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        tk.Label(zoom_frame, text="🔍 МАСШТАБ (ЗУМ)", bg="#1a1a3a", fg="#44aaff", 
                font=("Arial", 11, "bold")).pack()
        
        # Индикатор текущего zoom
        zoom_value_frame = tk.Frame(zoom_frame, bg="#1a1a3a")
        zoom_value_frame.pack(pady=2)
        
        tk.Label(zoom_value_frame, text="Текущий:", bg="#1a1a3a", fg="white", 
                font=("Arial", 8)).pack(side=tk.LEFT)
        
        self.zoom_value_label = tk.Label(zoom_value_frame, text="100%", bg="#1a1a3a", 
                                       fg="#00ff00", font=("Arial", 10, "bold"))
        self.zoom_value_label.pack(side=tk.LEFT, padx=5)
        
        tk.Label(zoom_frame, text="(влево - отдалить, вправо - приблизить)", 
                bg="#1a1a3a", fg="#888888", font=("Arial", 8)).pack()
        
        tk.Label(zoom_frame, text="(Правая кнопка мыши - изменение зума)", 
                bg="#1a1a3a", fg="#ffaa00", font=("Arial", 8, "bold")).pack()
        
        zoom_control = tk.Frame(zoom_frame, bg="#1a1a3a")
        zoom_control.pack(pady=5)
        
        # Иконки для зума (визуальные подсказки)
        tk.Label(zoom_control, text="🌌", bg="#1a1a3a", fg="white", 
                font=("Arial", 16)).pack(side=tk.LEFT, padx=2)
        
        # ИЗМЕНЕНО: обновили диапазон ползунка с 0.2-5.0 до 0.1-5.0
        self.zoom_scale = ttk.Scale(zoom_control, from_=0.1, to=5.0,  # Было 0.2, стало 0.1
                                    orient=tk.HORIZONTAL, length=250,
                                    command=self.change_zoom)
        self.zoom_scale.set(1.0)
        self.zoom_scale.pack(side=tk.LEFT, padx=5)
        
        tk.Label(zoom_control, text="🔬", bg="#1a1a3a", fg="white", 
                font=("Arial", 16)).pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = tk.Label(zoom_control, text="100%", bg="#1a1a3a", 
                                  fg="#00ff00", font=("Arial", 12, "bold"))
        self.zoom_label.pack(side=tk.LEFT, padx=10)
        
        # ИЗМЕНЕНО: обновили подсказки для отображения нового минимального зума
        # Подсказки по зуму (визуализация режимов)
        zoom_hint = tk.Frame(zoom_frame, bg="#1a1a3a")
        zoom_hint.pack(pady=5)
        
        hints = [
            ("10%", "Вся система (дальний обзор)", "#4444aa"),  # Было 20%, стало 10%
            ("50%", "Внутренние планеты", "#44aa44"),
            ("100%", "Обычный вид", "#aa44aa"),
            ("200%", "Детальный обзор", "#ffaa00"),
            ("300%", "Максимально близко", "#ff4444")
        ]
        
        for text, tip, color in hints:
            lbl = tk.Label(zoom_hint, text=text, bg=color, fg="white", 
                         font=("Arial", 8, "bold"), width=6)
            lbl.pack(side=tk.LEFT, padx=1)
            self.create_tooltip(lbl, tip)
        
        # Средний ряд - кнопки управления
        middle_row = tk.Frame(control_frame, bg="#1a1a3a")
        middle_row.pack(fill=tk.X, pady=5)
        
        # Группа кнопок 1 (управление симуляцией)
        group1 = tk.Frame(middle_row, bg="#1a1a3a")
        group1.pack(side=tk.LEFT, padx=10)
        
        buttons1 = [
            ("⏸ ПАУЗА", self.toggle_pause, "#ffaa00", "Остановить/продолжить движение"),
            ("🔄 СБРОС ВИДА", self.reset_view, "#44aa44", "Вернуть масштаб 100% и центр"),
            ("👁 ОРБИТЫ", self.toggle_orbits, "#4444aa", "Показать/скрыть орбиты")
        ]
        
        for text, cmd, color, tip in buttons1:
            btn = tk.Button(group1, text=text, command=cmd,
                          bg=color, fg="white", font=("Arial", 10, "bold"),
                          width=12, relief=tk.RAISED, borderwidth=2)
            btn.pack(side=tk.LEFT, padx=3)
            self.create_tooltip(btn, tip)
        
        # Группа кнопок 2 (режимы отображения)
        group2 = tk.Frame(middle_row, bg="#1a1a3a")
        group2.pack(side=tk.LEFT, padx=10)
        
        buttons2 = [
            ("📝 НАЗВАНИЯ", self.toggle_names, "#aa44aa", "Показать/скрыть названия"),
            ("✨ СЛЕДЫ", self.toggle_trails, "#aa4444", "Показать траекторию движения"),
            ("🎯 СЛЕДИТЬ", self.toggle_follow, "#44aaaa", "Камера следует за планетой")
        ]
        
        for text, cmd, color, tip in buttons2:
            btn = tk.Button(group2, text=text, command=cmd,
                          bg=color, fg="white", font=("Arial", 10, "bold"),
                          width=12, relief=tk.RAISED, borderwidth=2)
            btn.pack(side=tk.LEFT, padx=3)
            self.create_tooltip(btn, tip)
        
        # Кнопка центра Солнца
        sun_btn = tk.Button(middle_row, text="🌞 ЦЕНТР СОЛНЦА", 
                          command=self.center_on_sun,
                          bg="#ffaa00", fg="black", font=("Arial", 10, "bold"),
                          width=15, relief=tk.RAISED, borderwidth=2)
        sun_btn.pack(side=tk.LEFT, padx=10)
        self.create_tooltip(sun_btn, "Вернуться к виду от Солнца")
        
        # Нижний ряд - подсказки
        bottom_row = tk.Frame(control_frame, bg="#1a1a3a")
        bottom_row.pack(fill=tk.X, pady=5)
        
        hint_text = "💡 ПОДСКАЗКА: Зажмите ПРАВУЮ КНОПКУ МЫШИ и двигайте вверх/вниз для зума"
        hint_label = tk.Label(bottom_row, text=hint_text, bg="#1a1a3a", fg="#ffaa00",
                            font=("Arial", 10, "italic"))
        hint_label.pack()
    
    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """
        Создание всплывающей подсказки для элемента интерфейса.
        
        Args:
            widget: Элемент, для которого создается подсказка
            text: Текст подсказки
            
        Подсказка появляется при наведении курсора и исчезает при уходе.
        """
        def enter(event):
            # Позиционируем подсказку рядом с элементом
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Создаем окно подсказки без стандартного оформления
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, bg="#ffffaa", fg="black",
                           font=("Arial", 9), relief=tk.SOLID, borderwidth=1,
                           padx=5, pady=2)
            label.pack()
        
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    
    def create_left_panel(self) -> None:
        """
        Создание левой панели с кнопками планет.
        
        Панель содержит:
        - Кнопку Солнца
        - Кнопки всех планет (цветные)
        - Статистику симуляции
        """
        left_frame = tk.Frame(self.root, bg="#1a1a3a", width=180)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)
        
        tk.Label(left_frame, text="🚀 ПЛАНЕТЫ", bg="#1a1a3a", fg="white", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Кнопка Солнца
        sun_btn = tk.Button(left_frame, text="☀️ СОЛНЦЕ", bg="#ffaa00", fg="black",
                          font=("Arial", 12, "bold"), command=self.show_sun_info,
                          relief=tk.RAISED, borderwidth=3)
        sun_btn.pack(fill=tk.X, padx=5, pady=5)
        self.create_tooltip(sun_btn, "Информация о Солнце")
        
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Кнопки планет (сортируем по порядку от Солнца)
        for planet_name in self.planets_data.keys():
            color = self.planet_colors.get(planet_name, "#ffffff")
            btn = tk.Button(left_frame, text=f"● {planet_name}", bg=color, fg="black",
                          font=("Arial", 11, "bold"), 
                          command=lambda p=planet_name: self.show_planet_info(p),
                          relief=tk.RAISED, borderwidth=2)
            btn.pack(fill=tk.X, padx=5, pady=2)
            self.create_tooltip(btn, f"Информация о планете {planet_name}")
        
        # Статистика
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        tk.Label(left_frame, text="📊 СТАТИСТИКА", bg="#1a1a3a", fg="white", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        self.stats_text = tk.Label(left_frame, text="", bg="#1a1a3a", fg="#00ff00",
                                  font=("Arial", 10), justify=tk.LEFT)
        self.stats_text.pack(pady=5)
    
    def set_speed(self, value: float) -> None:
        """
        Установка скорости через кнопку-пресет.
        
        Args:
            value: Значение скорости (множитель)
            
        Синхронизирует ползунок и отображение скорости.
        """
        self.speed_scale.set(value)
        self.change_speed(value)
    
    def set_zoom(self, value: float) -> None:
        """
        Установка конкретного значения зума.
        
        Args:
            value: Значение масштаба (0.2-5.0)
            
        Синхронизирует ползунок и отображение масштаба.
        """
        self.zoom_scale.set(value)
        self.change_zoom(value)
    
    def change_speed(self, value: str) -> None:
        """
        Обработчик изменения скорости через ползунок.
        
        Args:
            value: Новое значение скорости (приходит как строка от Tkinter)
        """
        self.time_scale = float(value)
        self.speed_label.config(text=f"{self.time_scale:.1f}x")
    
    def change_zoom(self, value: str) -> None:
        """
        Обработчик изменения масштаба через ползунок.
        
        Args:
            value: Новое значение масштаба (приходит как строка от Tkinter)
        """
        self.target_zoom = float(value)
        self.zoom = self.target_zoom
        self.update_zoom_display()
        self.load_images()
    
    def toggle_pause(self) -> None:
        """Переключение режима паузы с сохранением времени."""
        self.paused = not self.paused
        if self.paused:
            self.pause_time = time.time()
        else:
            # Корректируем начальное время, чтобы избежать скачка при возобновлении
            self.start_time += (time.time() - self.pause_time)
    
    def toggle_orbits(self) -> None:
        """Переключение отображения орбит."""
        self.show_orbits = not self.show_orbits
    
    def toggle_names(self) -> None:
        """Переключение отображения названий планет."""
        self.show_names = not self.show_names
    
    def toggle_trails(self) -> None:
        """
        Переключение режима отображения следов движения.
        
        При выключении режима следы очищаются.
        """
        self.trail_mode = not self.trail_mode
        if not self.trail_mode:
            self.planet_trails.clear()
    
    def toggle_follow(self) -> None:
        """
        Переключение режима слежения за планетой.
        
        Если нет выбранной планеты, режим не включается.
        """
        self.follow_mode = not self.follow_mode
        if not self.follow_mode:
            self.selected_planet = None
    
    def center_on_sun(self) -> None:
        """Центрирование вида на Солнце."""
        self.selected_planet = None
        self.follow_mode = False
    
    def reset_view(self) -> None:
        """Сброс вида к начальным настройкам (масштаб 100%, центр на Солнце)."""
        self.target_zoom = 1.0
        self.zoom = 1.0
        self.zoom_scale.set(1.0)
        self.update_zoom_display()
        self.load_images()
        self.center_on_sun()
    
    def show_welcome_info(self) -> None:
        """
        Отображение приветственной информации с инструкциями.
        
        Показывается при запуске программы в информационной панели.
        """
        # Очищаем фото
        self.photo_label.config(image='')
        
        welcome = """
🌍 ДОБРО ПОЖАЛОВАТЬ В СИМУЛЯЦИЮ СОЛНЕЧНОЙ СИСТЕМЫ! 🌞

╔══════════════════════════════════╗
║         КАК ПОЛЬЗОВАТЬСЯ         ║
╚══════════════════════════════════╝

🔍 **ЗУМ (МАСШТАБ):**
• Зажмите ПРАВУЮ КНОПКУ МЫШИ и двигайте ВВЕРХ для приближения
• Двигайте ВНИЗ для отдаления
• Также можно использовать колесико мыши
• Ползунок МАСШТАБ внизу тоже работает
• Теперь можно отдалить до 10% для обзора всей системы!

⚡ **СКОРОСТЬ:**
• Ползунок СКОРОСТЬ - регулирует быстроту движения
• 0.1x - очень медленно, 1x - нормально, 10x - быстро

🎮 **РЕЖИМЫ:**
• ПАУЗА - остановить движение
• СБРОС ВИДА - вернуть масштаб 100%
• ОРБИТЫ - показать орбиты
• НАЗВАНИЯ - показать названия
• СЛЕДЫ - показать траекторию
• СЛЕДИТЬ - камера за планетой

🖱 **ДОПОЛНИТЕЛЬНО:**
• Кликните на планету - информация с фото
• Кнопки слева - быстрый выбор

ПРИЯТНОГО ИЗУЧЕНИЯ! 🚀
        """
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, welcome)
    
    def show_sun_info(self) -> None:
        """
        Отображение подробной информации о Солнце.
        
        Показывает:
        - Изображение Солнца (если есть)
        - Физические характеристики
        - Интересные факты
        """
        # Показываем фото Солнца если есть
        if self.info_images.get('Солнце'):
            self.photo_label.config(image=self.info_images['Солнце'])
        else:
            self.photo_label.config(image='')
        
        info = """
☀️ СОЛНЦЕ - ЗВЕЗДА СОЛНЕЧНОЙ СИСТЕМЫ ☀️

╔══════════════════════════════════╗
║        ОСНОВНЫЕ ПАРАМЕТРЫ        ║
╚══════════════════════════════════╝

📏 Диаметр: 1,392,700 км (в 109 раз больше Земли)
⚖ Масса: 1.99×10³⁰ кг (99.86% системы)
📊 Плотность: 1.41 г/см³
🌡 Температура: 5,500°C (поверхность)
🔥 Температура ядра: 15 млн°C

╔══════════════════════════════════╗
║         ХАРАКТЕРИСТИКИ           ║
╚══════════════════════════════════╝

🏷 Класс: Желтый карлик (G2V)
📅 Возраст: 4.6 млрд лет
🧪 Состав: Водород (74%), Гелий (24%)
🔄 Вращение: 25.05 дней (на экваторе)

╔══════════════════════════════════╗
║        ИНТЕРЕСНЫЕ ФАКТЫ          ║
╚══════════════════════════════════╝

✨ В Солнце поместится 1.3 млн Земель
✨ Свет достигает Земли за 8 мин 20 сек
✨ Каждую секунду теряет 4 млн тонн
✨ Энергии за час хватит человечеству на год

⚠️ ПРИМЕЧАНИЕ: 
В симуляции Солнце уменьшено для лучшего обзора планет
        """
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def show_planet_info(self, planet_name: str) -> None:
        """
        Отображение подробной информации о планете.
        
        Args:
            planet_name: Название планеты
            
        Показывает:
        - Изображение планеты (если есть)
        - Физические характеристики
        - Атмосферу и состав
        - Историю открытия
        - Краткое описание
        """
        p = self.planets_data[planet_name]
        
        # Показываем фото планеты если есть
        if self.info_images.get(planet_name):
            self.photo_label.config(image=self.info_images[planet_name])
        else:
            self.photo_label.config(image='')
        
        planet_emoji = {
            'Меркурий': '☿', 'Венера': '♀', 'Земля': '🌍',
            'Марс': '♂', 'Юпитер': '♃', 'Сатурн': '🪐',
            'Уран': '♅', 'Нептун': '♆'
        }
        
        info = f"{planet_emoji.get(planet_name, '●')} {planet_name.upper()} {planet_emoji.get(planet_name, '●')}\n"
        info += "╔══════════════════════════════════╗\n"
        info += "║        ОСНОВНЫЕ ПАРАМЕТРЫ        ║\n"
        info += "╚══════════════════════════════════╝\n\n"
        info += f"📏 Диаметр: {p['diameter']}\n"
        info += f"⚖ Масса: {p['mass']}\n"
        info += f"📊 Плотность: {p['density']}\n"
        info += f"🌡 Температура: {p['temperature']}\n"
        info += f"🎯 Гравитация: {p['gravity']}\n"
        info += f"🛸 Спутники: {p['moons']}\n\n"
        
        info += "╔══════════════════════════════════╗\n"
        info += "║         ХАРАКТЕРИСТИКИ           ║\n"
        info += "╚══════════════════════════════════╝\n\n"
        info += f"🌬 Атмосфера: {p['atmosphere']}\n"
        info += f"📅 Открытие: {p['discovery']}\n"
        info += f"🏷 Тип: {p['type']}\n\n"
        
        info += "╔══════════════════════════════════╗\n"
        info += "║           ОПИСАНИЕ               ║\n"
        info += "╚══════════════════════════════════╝\n\n"
        info += f"{p['description']}"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        
        self.selected_planet = planet_name
        if self.follow_mode:
            self.follow_mode = True
    
    def update_stats(self, sim_years: float) -> None:
        """
        Обновление статистики в левой панели.
        
        Args:
            sim_years: Текущее время симуляции в годах
            
        Отображает:
        - Время симуляции
        - Скорость и масштаб
        - Режим масштаба
        - Статус (работает/пауза)
        """
        status_color = "#00ff00" if not self.paused else "#ffaa00"
        status_text = "▶ РАБОТАЕТ" if not self.paused else "⏸ ПАУЗА"
        
        # ИЗМЕНЕНО: обновили режимы зума для нового минимального значения
        # Определяем режим зума по величине масштаба
        if self.zoom < 0.3:
            zoom_mode = "🌌 Вся система (дальний)"
        elif self.zoom < 0.5:
            zoom_mode = "🪐 Дальний обзор"
        elif self.zoom < 1.0:
            zoom_mode = "🪐 Внутренние планеты"
        elif self.zoom < 1.5:
            zoom_mode = "🔭 Обычный"
        elif self.zoom < 2.0:
            zoom_mode = "🔬 Детальный"
        else:
            zoom_mode = "⚡ Максимальный"
        
        stats = f"⏱ Время: {sim_years:.1f} лет\n"
        stats += f"⚡ Скорость: {self.time_scale:.1f}x\n"
        stats += f"🔍 Масштаб: {int(self.zoom*100)}%\n"
        stats += f"📊 Режим: {zoom_mode}\n"
        stats += f"🪐 Планет: 8\n"
        stats += f"🌕 Спутников: >200\n"
        stats += f"📊 Статус: {status_text}"
        
        self.stats_text.config(text=stats, fg=status_color)
        self.sim_time_label.config(text=f"{sim_years:.2f} лет")
    
    def get_planet_position(self, planet_name: str, time_angle: float) -> Tuple[float, float, float]:
        """
        Расчет позиции планеты на орбите в заданный момент времени.
        
        Args:
            planet_name: Название планеты
            time_angle: Текущее время симуляции (в условных единицах)
            
        Returns:
            Tuple[float, float, float]: (x, y, angle) - координаты и угол поворота
            
        Физическая модель:
        - Орбиты представлены как окружности (упрощение)
        - Координаты: x = distance * cos(angle), y = distance * sin(angle)
        - Вид сверху (без сжатия по вертикали)
        - Угол зависит от периода обращения: angle = (time / period) * 2π
        """
        planet = self.planets_data[planet_name]
        # Расстояние от Солнца с учетом масштаба
        distance = planet['distance'] * self.AU * self.zoom
        # Угол на орбите (в радианах)
        angle = time_angle / planet['orbit_period'] * 2 * math.pi
        
        # Координаты для вида сверху (без сжатия по вертикали)
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)  # Вид сверху - без коэффициента сжатия
        
        return x, y, angle
    
    def draw_planet(self, planet_name: str, x: float, y: float, angle: float) -> None:
        """
        Отрисовка планеты и связанных с ней элементов.
        
        Args:
            planet_name: Название планеты
            x: Координата X относительно центра холста
            y: Координата Y относительно центра холста
            angle: Текущий угол на орбите
            
        Отрисовывает:
        - След движения (если включен)
        - Орбиту (если включена)
        - Изображение планеты или круг с эффектом свечения
        - Название (если включено)
        """
        planet = self.planets_data[planet_name]
        radius = self.EARTH_RADIUS * planet['size_ratio'] * self.zoom
        
        # Центр холста
        cx = self.canvas.winfo_width() // 2
        cy = self.canvas.winfo_height() // 2
        
        # Абсолютные координаты на холсте
        px = cx + x
        py = cy + y
        
        # ===== СЛЕДЫ =====
        if self.trail_mode:
            # Инициализируем список следов для планеты, если его нет
            if planet_name not in self.planet_trails:
                self.planet_trails[planet_name] = []
            # Добавляем текущую позицию
            self.planet_trails[planet_name].append((px, py))
            # Ограничиваем длину следа 100 точками
            if len(self.planet_trails[planet_name]) > 100:
                self.planet_trails[planet_name].pop(0)
            
            # Рисуем след (линии между последовательными позициями)
            trail = self.planet_trails[planet_name]
            if len(trail) > 1:
                for i in range(len(trail)-1):
                    self.canvas.create_line(trail[i][0], trail[i][1],
                                          trail[i+1][0], trail[i+1][1],
                                          fill=planet['color'], width=1)
        
        # ===== ОРБИТА =====
        if self.show_orbits:
            orbit_radius = planet['distance'] * self.AU * self.zoom
            # Рисуем круглую орбиту для вида сверху
            self.canvas.create_oval(cx - orbit_radius, cy - orbit_radius,
                                   cx + orbit_radius, cy + orbit_radius,
                                   outline="#446688", width=1, dash=(3, 6))
        
        # ===== ПЛАНЕТА =====
        # Используем изображение если доступно
        if self.planet_images.get(planet_name):
            img = self.canvas.create_image(px, py, image=self.planet_images[planet_name])
            # Привязываем клик по изображению к показу информации
            self.canvas.tag_bind(img, "<Button-1>", 
                                lambda e, p=planet_name: self.show_planet_info(p))
        else:
            # Если нет изображения, рисуем круг с эффектом свечения
            # Эффект свечения - несколько концентрических окружностей с разной прозрачностью
            for i in range(3, 0, -1):
                glow_radius = radius * (1 + i * 0.1)
                # Цвет свечения - тот же, что у планеты, но без обводки
                self.canvas.create_oval(px - glow_radius, py - glow_radius,
                                       px + glow_radius, py + glow_radius,
                                       fill=planet['color'], outline="", width=0)
            
            # Ядро планеты с белой обводкой для контраста
            planet_obj = self.canvas.create_oval(px - radius, py - radius,
                                                px + radius, py + radius,
                                                fill=planet['color'], 
                                                outline="white", width=1)
            # Привязываем клик по кругу к показу информации
            self.canvas.tag_bind(planet_obj, "<Button-1>", 
                                lambda e, p=planet_name: self.show_planet_info(p))
        
        # ===== НАЗВАНИЕ =====
        if self.show_names:
            text = self.canvas.create_text(px, py - radius - 15, text=planet_name,
                                         fill="white", font=("Arial", 9, "bold"))
            # Клик по названию также показывает информацию
            self.canvas.tag_bind(text, "<Button-1>", 
                                lambda e, p=planet_name: self.show_planet_info(p))
        
        # Сохраняем текущий угол для возможного использования в будущем
        self.planet_angles[planet_name] = angle
    
    def draw_sun(self) -> None:
        """
        Отрисовка Солнца в центре холста.
        
        Особенности:
        - Если доступно изображение - использует его
        - Иначе рисует круг с эффектом свечения (градиент из желтых оттенков)
        - Добавляет подпись
        - Привязывает обработчик клика
        """
        cx = self.canvas.winfo_width() // 2
        cy = self.canvas.winfo_height() // 2
        radius = self.SUN_RADIUS * self.zoom
        
        # Солнце теперь еще меньше для лучшей видимости дальних планет
        if self.planet_images.get('Солнце'):
            sun_img = self.canvas.create_image(cx, cy, image=self.planet_images['Солнце'])
            self.canvas.tag_bind(sun_img, "<Button-1>", lambda e: self.show_sun_info())
        else:
            # Эффект свечения - несколько слоев с уменьшающейся яркостью
            for i in range(3, 0, -1):
                glow_radius = radius * (1 + i * 0.1)
                # Чем дальше слой, тем прозрачнее (управляется HEX-значением)
                alpha = int(100 / i)
                color = f'#ffff{alpha:02x}'  # Желтый с разной яркостью
                self.canvas.create_oval(cx - glow_radius, cy - glow_radius,
                                       cx + glow_radius, cy + glow_radius,
                                       fill=color, outline="")
            
            # Ядро Солнца
            sun_core = self.canvas.create_oval(cx - radius, cy - radius,
                                              cx + radius, cy + radius,
                                              fill="#ffaa00", outline="#ff6600", width=1)
            self.canvas.tag_bind(sun_core, "<Button-1>", lambda e: self.show_sun_info())
        
        # Надпись
        text = self.canvas.create_text(cx, cy - radius - 20, text="☀️ СОЛНЦЕ ☀️",
                                      fill="yellow", font=("Arial", 10, "bold"))
        self.canvas.tag_bind(text, "<Button-1>", lambda e: self.show_sun_info())
    
    def update(self) -> None:
        """
        Главный метод обновления анимации.
        
        Вызывается каждые 50 мс через self.root.after().
        Отвечает за:
        - Расчет текущего времени симуляции
        - Обновление статистики
        - Очистку и перерисовку всех объектов
        - Планирование следующего обновления
        
        Частота обновления: ~20 FPS (50 мс между кадрами)
        """
        if not self.running:
            return
        
        # Расчет времени симуляции
        if not self.paused:
            # Время с учетом множителя скорости
            current_time = (time.time() - self.start_time) * self.time_scale
            # Конвертация в годы (10 - масштабный коэффициент для наглядности)
            sim_years = current_time / (365.25 * 24 * 3600 * 10)
        else:
            # В режиме паузы время не меняется
            current_time = self.pause_time
            sim_years = self.pause_time / (365.25 * 24 * 3600 * 10)
        
        # Обновляем статистику
        self.update_stats(sim_years)
        
        # Очищаем холст
        self.canvas.delete("all")
        
        # Отрисовываем только если холст имеет разумные размеры
        if self.canvas.winfo_width() > 1 and self.canvas.winfo_height() > 1:
            self.draw_sun()
            
            # Сортируем планеты по расстоянию от Солнца
            # Это важно для правильного перекрытия (ближние планеты рисуются поверх дальних)
            sorted_planets = sorted(self.planets_data.keys(),
                                   key=lambda p: self.planets_data[p]['distance'])
            
            # Отрисовываем каждую планету
            for planet_name in sorted_planets:
                x, y, angle = self.get_planet_position(planet_name, current_time)
                self.draw_planet(planet_name, x, y, angle)
        
        # Планируем следующее обновление через 50 мс
        self.root.after(50, self.update)


def main() -> None:
    """
    Главная функция запуска приложения.
    
    Создает главное окно, инициализирует симуляцию
    и запускает главный цикл обработки событий Tkinter.
    """
    root = tk.Tk()
    app = SolarSystemSimulation(root)
    
    def on_closing() -> None:
        """Корректное завершение работы при закрытии окна."""
        app.running = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()