"""
Patient Database Management
支援民國年月日的病患資料庫
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict
from loguru import logger
from pathlib import Path
import json


class ROCDateConverter:
    """民國年月日轉換器"""
    
    @staticmethod
    def gregorian_to_roc(year: int, month: int, day: int) -> str:
        """西元年轉民國年
        
        Args:
            year: 西元年
            month: 月
            day: 日
        
        Returns:
            民國年月日字符串 (例如: "115年07月29日")
        """
        roc_year = year - 1911
        return f"{roc_year}年{month:02d}月{day:02d}日"
    
    @staticmethod
    def roc_to_gregorian(roc_str: str) -> tuple:
        """民國年轉西元年
        
        Args:
            roc_str: 民國年字符串 (例如: "115年07月29日" 或 "115/07/29")
        
        Returns:
            (year, month, day) tuple
        """
        # 支援多種格式
        roc_str = roc_str.replace('年', '/').replace('月', '/').replace('日', '')
        parts = roc_str.split('/')
        
        if len(parts) >= 3:
            roc_year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            year = roc_year + 1911
            return (year, month, day)
        else:
            raise ValueError(f"Invalid ROC date format: {roc_str}")
    
    @staticmethod
    def today_roc() -> str:
        """獲取今天的民國日期"""
        today = date.today()
        return ROCDateConverter.gregorian_to_roc(today.year, today.month, today.day)


class PatientDatabase:
    """病患資料庫管理"""
    
    def __init__(self, db_path: str = "data/patients.db"):
        self.db_path = db_path
        
        # 確保資料夾存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化資料庫
        self._init_database()
        logger.info(f"Patient database initialized: {db_path}")
    
    def _init_database(self):
        """初始化資料庫表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 病患資料表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                birth_date_roc TEXT NOT NULL,
                birth_date_gregorian TEXT NOT NULL,
                id_number TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                blood_type TEXT,
                allergies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 掛號紀錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT UNIQUE NOT NULL,
                patient_id TEXT NOT NULL,
                department TEXT NOT NULL,
                doctor TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)
        
        # 醫師資料表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                specialty TEXT,
                schedule TEXT,
                available_days TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_patient(
        self,
        name: str,
        birth_date_roc: str,
        id_number: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        emergency_phone: Optional[str] = None,
        blood_type: Optional[str] = None,
        allergies: Optional[str] = None
    ) -> Dict:
        """新增病患
        
        Args:
            name: 姓名
            birth_date_roc: 出生日期（民國）
            id_number: 身分證號
            phone: 電話
            address: 地址
            emergency_contact: 緊急聯絡人
            emergency_phone: 緊急聯絡電話
            blood_type: 血型
            allergies: 過敏史
        
        Returns:
            病患資料字典
        """
        try:
            # 轉換民國年為西元年
            year, month, day = ROCDateConverter.roc_to_gregorian(birth_date_roc)
            birth_date_gregorian = f"{year}-{month:02d}-{day:02d}"
            
            # 生成病患ID
            patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO patients (
                    patient_id, name, birth_date_roc, birth_date_gregorian,
                    id_number, phone, address, emergency_contact, emergency_phone,
                    blood_type, allergies
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id, name, birth_date_roc, birth_date_gregorian,
                id_number, phone, address, emergency_contact, emergency_phone,
                blood_type, allergies
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Patient added: {patient_id} - {name}")
            
            return {
                "success": True,
                "patient_id": patient_id,
                "name": name,
                "birth_date_roc": birth_date_roc
            }
        
        except Exception as e:
            logger.error(f"Failed to add patient: {e}")
            return {"success": False, "error": str(e)}
    
    def update_patient(
        self,
        patient_id: str,
        **kwargs
    ) -> Dict:
        """更新病患資料
        
        Args:
            patient_id: 病患ID
            **kwargs: 要更新的欄位
        
        Returns:
            更新結果
        """
        try:
            # 如果更新出生日期，需要轉換
            if 'birth_date_roc' in kwargs:
                year, month, day = ROCDateConverter.roc_to_gregorian(kwargs['birth_date_roc'])
                kwargs['birth_date_gregorian'] = f"{year}-{month:02d}-{day:02d}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 動態生成 UPDATE 語句
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(patient_id)
            
            cursor.execute(f"""
                UPDATE patients
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE patient_id = ?
            """, values)
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            if affected_rows > 0:
                logger.info(f"Patient updated: {patient_id}")
                return {"success": True, "patient_id": patient_id}
            else:
                return {"success": False, "error": "Patient not found"}
        
        except Exception as e:
            logger.error(f"Failed to update patient: {e}")
            return {"success": False, "error": str(e)}
    
    def get_patient(self, patient_id: Optional[str] = None, name: Optional[str] = None) -> Optional[Dict]:
        """查詢病患"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if patient_id:
                cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
            elif name:
                cursor.execute("SELECT * FROM patients WHERE name LIKE ?", (f"%{name}%",))
            else:
                return None
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        
        except Exception as e:
            logger.error(f"Failed to get patient: {e}")
            return None
    
    def create_appointment(
        self,
        patient_id: str,
        department: str,
        doctor: str,
        appointment_date: str,
        appointment_time: str,
        notes: Optional[str] = None
    ) -> Dict:
        """建立掛號"""
        try:
            appointment_id = f"A{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO appointments (
                    appointment_id, patient_id, department, doctor,
                    appointment_date, appointment_time, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                appointment_id, patient_id, department, doctor,
                appointment_date, appointment_time, notes
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Appointment created: {appointment_id}")
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "department": department,
                "doctor": doctor,
                "date": appointment_date,
                "time": appointment_time
            }
        
        except Exception as e:
            logger.error(f"Failed to create appointment: {e}")
            return {"success": False, "error": str(e)}
    
    def get_doctor_schedule(self, department: Optional[str] = None) -> List[Dict]:
        """查詢醫師排班"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if department:
                cursor.execute("SELECT * FROM doctors WHERE department = ?", (department,))
            else:
                cursor.execute("SELECT * FROM doctors")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Failed to get doctor schedule: {e}")
            return []


def init_fake_data():
    """初始化假資料"""
    db = PatientDatabase()
    
    # 假的病患資料
    fake_patients = [
        {
            "name": "王小明",
            "birth_date_roc": "80年05月15日",
            "id_number": "A123456789",
            "phone": "0912345678",
            "address": "台北市信義區信義路五段7號",
            "blood_type": "A型",
            "allergies": "青黴素"
        },
        {
            "name": "李美玲",
            "birth_date_roc": "75年12月20日",
            "id_number": "B234567890",
            "phone": "0923456789",
            "address": "新北市板橋區中山路一段161號",
            "blood_type": "O型",
            "allergies": "無"
        },
        {
            "name": "張大華",
            "birth_date_roc": "65年08月10日",
            "id_number": "C345678901",
            "phone": "0934567890",
            "address": "台中市西屯區台灣大道三段99號",
            "blood_type": "B型",
            "allergies": "花生"
        },
        {
            "name": "陳雅婷",
            "birth_date_roc": "90年03月25日",
            "id_number": "D456789012",
            "phone": "0945678901",
            "address": "高雄市左營區博愛二路777號",
            "blood_type": "AB型",
            "allergies": "海鮮"
        },
        {
            "name": "林志明",
            "birth_date_roc": "70年11月08日",
            "id_number": "E567890123",
            "phone": "0956789012",
            "address": "台南市東區東門路一段300號",
            "blood_type": "A型",
            "allergies": "無"
        }
    ]
    
    for patient in fake_patients:
        db.add_patient(**patient)
    
    # 假的醫師資料
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    fake_doctors = [
        ("D001", "王建國", "心臟內科", "心血管疾病", "週一至週五 09:00-12:00", "週一,週二,週三,週四,週五"),
        ("D002", "李淑芬", "神經內科", "頭痛、失眠", "週一至週四 14:00-17:00", "週一,週二,週三,週四"),
        ("D003", "張志偉", "骨科", "骨折、關節炎", "週二至週六 09:00-12:00", "週二,週三,週四,週五,週六"),
        ("D004", "陳美玲", "小兒科", "兒童疾病", "週一至週五 14:00-17:00", "週一,週二,週三,週四,週五"),
        ("D005", "林建華", "婦產科", "產檢、婦科疾病", "週一至週五 09:00-12:00, 14:00-17:00", "週一,週二,週三,週四,週五"),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO doctors (doctor_id, name, department, specialty, schedule, available_days)
        VALUES (?, ?, ?, ?, ?, ?)
    """, fake_doctors)
    
    conn.commit()
    conn.close()
    
    logger.info("Fake data initialized successfully")


if __name__ == "__main__":
    # 測試
    init_fake_data()
    
    db = PatientDatabase()
    
    # 測試查詢
    patient = db.get_patient(name="王小明")
    print("查詢病患:", json.dumps(patient, ensure_ascii=False, indent=2))
    
    # 測試建立掛號
    if patient:
        result = db.create_appointment(
            patient_id=patient['patient_id'],
            department="心臟內科",
            doctor="王建國",
            appointment_date="115/08/01",
            appointment_time="09:30"
        )
        print("建立掛號:", json.dumps(result, ensure_ascii=False, indent=2))
