import cv2
import pytesseract
import pandas as pd
import sys

POSSIBLE_UNITS = ("L", "ML", "G", "GRAM", "KG")

class ReceiptItem:
    def __init__(self):
        self.item = None
        self.qty = 1
        self.price = None
    
    def __str__(self):
        return str((self.item, self.qty, self.price))

    def __repr__(self):
        return str(self)
    
    def to_dict(self):
        return {'Name':self.item, 'Quantity':self.qty, 'Price':self.price}


def parse_raw_text(text):
    # Parse lines and clean them
    lines = text.upper().split("\n")
    items = []

    curr_item = ReceiptItem()
    for l in lines:
        if len(l) < 4:
            continue
        if " EACH" in l or "@" in l:
            # Quantity line
            l_split = l.split()
            # Extract total price if it is on this line
            price = l_split[-1]
            try:
                if "." in price:
                    price = float(price)
                    curr_item.price = price
            except ValueError:
                pass
            # Extract quantity either using @ sign or total price/each price
            if "@" in l:
                qty = l.split("@")[0].strip().split()[-1]
                if qty.isdigit():
                    qty = int(qty)
                    curr_item.qty = qty
            else:
                each_price = l.split("EACH")[0].strip().split()[-1].strip('$')
                try:
                    each_price = float(each_price)
                    qty = int(curr_item.price/each_price)
                    curr_item.qty = qty
                except ValueError:
                    pass
        else:
            # New product. Store current product if it has data.
            if curr_item.item:
                items.append(curr_item)
            # Record new product
            curr_item = ReceiptItem()
            l_split = l.split()
            price = l_split[-1]
            try:
                if "." in price:
                    price = float(price)
                    curr_item.price = price
                    l_split = l_split[:-1]
            except ValueError:
                pass
            curr_item.item = " ".join(l_split)

    if curr_item.item:
        items.append(curr_item)
    return items

def parse_image(img_filename):
    img = cv2.imread(img_filename)
    text = pytesseract.image_to_string(img, lang='eng', config='--psm 6 --oem 1 -c tessedit_char_blacklist=|{}()[],')
    items = parse_raw_text(text)
    items_df = pd.DataFrame.from_records([i.to_dict() for i in items])
    return items_df
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No file inputted.")
    filename = sys.argv[1]
    df = parse_image(filename)
    if len(sys.argv) < 3:
        print(df)
    else:
        save_file = sys.argv[2]
        df.to_csv(save_file)
