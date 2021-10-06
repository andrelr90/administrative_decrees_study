from pathlib import Path
import io

class FileController:
    @staticmethod
    def save_decreto_file(year, name, content):
        folder = Path("/home/andre/radar/radar_dev/decretos/"+str(year)+"/")
        name = folder / (name+".html")
        f = io.open(name, mode="wb")
        f.write(content)
        f.close()
    
    @staticmethod
    def save_data_file(year, name, content):
        folder = Path("/home/andre/radar/radar_dev/decretos/"+str(year)+"/")
        name = folder / (name+"_data.html")
        f = io.open(name, mode="wb")
        f.write(content)
        f.close()