import datetime
import re


class TransformData:
    """
    Classe que contém funções que manipulam atributos de documentos do banco de dados.
    """
    @staticmethod
    def cvt_timestampz_to_date(date_field):
        """
        Função que formata datas de tipo TIMESTAMPZ para DATE.
        """
        if date_field is None:
            return None

        if isinstance(date_field, datetime.datetime):
            return date_field.date()

        return date_field
    
    @staticmethod
    def cvt_inverted_date(date_field) -> None:
        """
        Formata datas que estão em DD-MM-YYYY para YYYY-MM-DD.
        """
        if date_field is None:
            return None
        
        date = str(date_field).strip()

        if re.match(r'..-..-20[0-2][0-9]', date):
            return f"{date[6:10]}-{date[3:5]}-{date[0:2]}"
        
        return date

    @staticmethod
    def clean_string(date_field):
        """
        Remove espaços em branco de datas.
        """
        if date_field is None:
            return None
        
        return str(date_field).strip()

    @staticmethod
    def string_date_processing(date_field) -> None:
        """
        Transforma data de 'DD de MM de YYYY' para 'DD-MM-YYYY'

        Esta função foi criada porque a data de publicação do portal Diário da Manhã possui a formatação citada acima.
        """
        if date_field is None:
            return None

        dict_month = {
            "janeiro" : "01",
            "fevereiro" : "02",
            "março" : "03",
            "abril" : "04",
            "maio" : "05",
            "junho" : "06",
            "julho" : "07",
            "agosto" : "08",
            "setembro" : "09",
            "outubro" : "10",
            "novembro" : "11",
            "dezembro" : "12"
        }
        
        date = str(date_field).lower().strip()

        if "de" in date.split(" "):
            date = re.sub(r' de ', '-', date)

            for month in dict_month:
                if re.findall(fr"{month}", date):
                    date = re.sub(fr"{month}", dict_month[month], date)
                    break

            if len(date) == 9:
                date = "0" + date
            
        return date
    
    def bar_date_processing(date_field):
        if date_field is None:
            return None
        
        date_field = re.sub(r"/", "-", date_field)

        return date_field
