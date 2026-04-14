import json # Перенесли в начало
from quiz_data import questions
import qrcode
from PIL import Image, ImageDraw, ImageFont

class QuizManager:
    def __init__(self):
        self.user_states = {}

    def check_user(self, user_id):
        """Проверяем, есть ли юзер в базе опекунов"""
        try:
            with open('/content/guardians.json', 'r') as f:
                data = json.load(f)
                return data.get(str(user_id)) 
        except:
            return None

    def start_quiz(self, user_id):
        self.user_states[user_id] = {
            'current_question': 1,
            'scores': {
                'tur': 0, 'frog': 0, 'turtle': 0, 'magpie': 0, 'viper': 0
            }
        }

    def get_question(self, user_id):
        q_id = self.user_states[user_id]['current_question']
        return questions.get(q_id)

    def update_score(self, user_id, animal_key):
        if user_id not in self.user_states:
            self.start_quiz(user_id)
        self.user_states[user_id]['scores'][animal_key] += 1
        self.user_states[user_id]['current_question'] += 1

    def get_result(self, user_id):
        # Если юзера нет в оперативной памяти (после перезапуска бота)
        if user_id not in self.user_states:
            # Пытаемся восстановить данные из JSON
            user_data = self.check_user(user_id)
            if user_data:
                # Если нашли в базе - берем тотем оттуда
                return user_data['totem']
            else:
                # Если и там нет - возвращаем None или дефолт
                return None

        # Обычный расчет по баллам
        scores = self.user_states[user_id]['scores']
        return max(scores, key=scores.get)


    def is_last_question(self, user_id):
        return self.user_states[user_id]['current_question'] > len(questions)

    # ТЕПЕРЬ ОН ВНУТРИ КЛАССА (с отступами!)
    # ДОБАВЬ animal_name В СКОБКИ
    def save_result(self, user_id, user_name, animal_name): 
        # Теперь Python видит, что аргументов должно быть 4 (включая self)
        try:
            with open('/content/guardians.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}

        data[str(user_id)] = {
            "name": user_name,
            "totem": animal_name # Используем переданное имя
        }

        with open('/content/guardians.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def create_certificate(self, user_name, animal_name):
        from PIL import Image, ImageDraw, ImageFont
        
        # 1. Создаем холст 1000x700
        img = Image.new('RGB', (1000, 700), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 2. РОВНОЕ ЛОГО СПРАВА СНИЗУ
        try:
            logo = Image.open('/content/images/question.png').convert("RGBA")
            # Пропорционально меняем размер (чтобы не было сплющено)
            logo.thumbnail((180, 180), Image.Resampling.LANCZOS)
            # Рассчитываем позицию с отступом 40 пикселей от края
            logo_x = 1000 - logo.width - 60
            logo_y = 700 - logo.height - 60
            img.paste(logo, (logo_x, logo_y), logo) 
        except Exception as e:
            print(f"Ошибка лого: {e}")

        # 3. ШРИФТЫ (С ПРОВЕРКОЙ КИРИЛЛИЦЫ)
        try:
            # Убедись, что эти файлы лежат в корне Колаба!
            font_header = ImageFont.truetype("/content/ALS_Story_2.0_B.otf", 55)
            font_main = ImageFont.truetype("/content/ALS_Story_2.0_R.otf", 35)
        except:
            # Резервный системный шрифт, который 100% тянет русский
            font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
            font_header = ImageFont.truetype(font_path, 55)
            font_main = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 35)

        # 4. ДИЗАЙН (Золотая рамка и текст)
        # Золотая рамка
        draw.rectangle([20, 20, 980, 680], outline=(255, 215, 0), width=5)
        
        # Текст по центру (anchor="mm" - выравнивание по середине)
                # Текст (Золотой и Белый)
                # Текст (Золотой и Белый)
        draw.text((500, 120), "СЕРТИФИКАТ ХРАНИТЕЛЯ", fill=(255, 215, 0), font=font_header, anchor="mm")
        
        # Вместо "настоящим"
        draw.text((500, 250), "Отныне и навсегда", fill=(255, 255, 255), font=font_main, anchor="mm")
        
        # Имя (Крупно и Золото)
        draw.text((500, 350), f"{user_name}", fill=(255, 215, 0), font=font_header, anchor="mm")
        
        # Переход
        draw.text((500, 460), "берет под свою опеку", fill=(255, 255, 255), font=font_main, anchor="mm")
        
        # Животное (Мощно)
        draw.text((500, 560), f"{animal_name.upper()}", fill=(255, 215, 0), font=font_header, anchor="mm")

        cert_path = f"/content/cert_{user_name}.png"
        qr_url = "https://moscowzoo.ru"
        qr = qrcode.QRCode(box_size=4, border=1) # Маленький размер для угла
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="gold", back_color="black").convert("RGBA")
    
    # 2. Накладываем QR-код (например, в левый нижний угол)
        img.paste(qr_img, (60, 500), qr_img)

        img.save(cert_path)
        return cert_path


