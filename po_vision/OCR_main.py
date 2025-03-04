from paddleocr import PaddleOCR
from OCR_txt_utils import *
from OCR_ui_exactors import *
from Company_Checker import company_checker_main
from Error_handler import safe_extractor
import cv2
import json
import logging


keyword_mapping_dict = {
    "PONO": {
        "keywords": ["PONO", "請購單號", "請購", "交貨"]
    },
    "PRODUCT": {
        "keywords": ["PRODUCT", "規格"]
    },
    "QUANTITY": {
        "keywords": ["QUANTITY", "數量"]
    },
    "BATCH NUMBER": {
        "keywords": ["BATCH NUMBER", "型號", "批號"]
    },
    "EXPIRY DATE": {
        "keywords": ["EXPIRY DATE", "EXPIRY", "效期"]
    }
}


def po_vision_main(image_path):

    # Initial OCR reader and text processor
    ocr_reader = PaddleOCR(use_angle_cls=True, lang='ch')
    processor = TextProcessor()

    # image processing
    image_height, image_width, _ = image_path.shape

    # image_common = cut_roi_by_ratio(image_path, 0.1, 0.4)
    image_common_text_traditional = processor.convert_to_traditional(txt_extract(image_path, ocr_reader))
    logging.info(f'origin text: {image_common_text_traditional}')

    # Check Company Info
    company, direction = company_checker_main(image_common_text_traditional)
    logging.info(f'Company: {company}')

    get_keyword_in_image = match_keywords(keyword_mapping_dict, image_common_text_traditional, processor)
    logging.info(f"Keywords position: {get_keyword_in_image}")

    aligned_same_column = group_same_column_by_keywords(get_keyword_in_image, image_common_text_traditional)
    logging.info(f"Text in same column: {aligned_same_column}")

    merge_same_row_from_aligned = merge_same_row(aligned_same_column)
    logging.info(f"Merger same row: {merge_same_row_from_aligned}")

    # 提取數量和批號
    try:
        qty, qty_conf, qty_coord = safe_extractor(quantity_extractor, merge_same_row_from_aligned, 'QUANTITY')
    except (KeyError, IndexError, ValueError) as e:
        logging.error(f'name fail: {e}')
        qty, qty_conf, qty_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]
    try:
        batch_num, batch_num_conf, batch_num_coord = safe_extractor(batch_num_extractor, merge_same_row_from_aligned, 'BATCH NUMBER')
    except (KeyError, IndexError, ValueError) as e:
        logging.error(f'name fail: {e}')
        batch_num, batch_num_conf, batch_num_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

    # 提取請購單號
    if company == "大昌":
        try:
            po_num, po_num_conf, po_num_coord = safe_extractor(po_number_extractor_cht, image_common_text_traditional, "請購")
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            po_num, po_num_conf, po_num_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

        try:
            expiry_date, expiry_date_conf, expiry_date_coord = safe_extractor(expiry_date_extractor_cht, merge_same_row_from_aligned, 'EXPIRY DATE')
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            expiry_date, expiry_date_conf, expiry_date_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

    elif not company:
        try:
            po_num, po_num_conf, po_num_coord = safe_extractor(po_number_extractor_cht, image_common_text_traditional, "交貨")
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            po_num, po_num_conf, po_num_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

        try:
            expiry_date, expiry_date_conf, expiry_date_coord = safe_extractor(expiry_date_extractor_en, merge_same_row_from_aligned, 'EXPIRY DATE')
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            expiry_date, expiry_date_conf, expiry_date_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

    else:
        try:
            po_num, po_num_conf, po_num_coord = safe_extractor(po_number_extractor_en, merge_same_row_from_aligned, 'PONO', processor)
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            po_num, po_num_conf, po_num_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

        try:
            expiry_date, expiry_date_conf, expiry_date_coord = safe_extractor(expiry_date_extractor_en, merge_same_row_from_aligned, 'EXPIRY DATE')
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            expiry_date, expiry_date_conf, expiry_date_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]


    # 提取產品資訊
    if company == "中外":
        try:
            name, name_conf, name_coord = product_info_extractor_cht_first(merge_same_row_from_aligned, 'PRODUCT')
            en_name, en_name_conf, en_name_coord  = name[0], name_conf[0], name_coord[0]
            cht_name, cht_name_conf, cht_name_coord = name[1], name_conf[1], name_coord[1]
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            en_name, en_name_conf, en_name_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]
            cht_name, cht_name_conf, cht_name_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

    else:
        try:
            name, name_conf, name_coord = product_info_extractor_en_first(merge_same_row_from_aligned, 'PRODUCT')
            en_name, en_name_conf, en_name_coord = name[0], name_conf[0], name_coord[0]
            cht_name, cht_name_conf, cht_name_coord = name[1], name_conf[1], name_coord[1]
        except (KeyError, IndexError, ValueError) as e:
            logging.error(f'name fail: {e}')
            en_name, en_name_conf, en_name_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]
            cht_name, cht_name_conf, cht_name_coord = "", 0, [[0, 0], [0, 0], [0, 0], [0, 0]]

    batch_expiry_bool = not (batch_num == "" or expiry_date == "")
    print("--------------------")
    print(batch_expiry_bool)
    print("--------------------")
    result_dict = {
        "po_num": po_num,
        "po_num_conf": str(po_num_conf),
        "po_num_coord": ";".join([f"{int(x)},{int(y)}" for x, y in po_num_coord]),

        "name": en_name,
        "name_conf": str(en_name_conf),
        "name_coord": ";".join(
            [f"{int(x)},{int(y)}" for x, y in en_name_coord]),

        "cht_name": cht_name,
        "cht_name_conf": str(cht_name_conf),
        "cht_name_coord": ";".join(
            [f"{int(x)},{int(y)}" for x, y in cht_name_coord]),

        "qty": qty,
        "qty_conf": str(qty_conf),
        "qty_coord": ";".join(
            [f"{int(x)},{int(y)}" for x, y in qty_coord]),

        "batch_num": batch_num,
        "batch_num_conf": str(batch_num_conf),
        "batch_num_coord": ";".join(
            [f"{int(x)},{int(y)}" for x, y in batch_num_coord]),

        "expirydate": expiry_date,
        "expirydate_conf": str(expiry_date_conf),
        "expirydate_coord": ";".join(
            [f"{int(x)},{int(y)}" for x, y in expiry_date_coord])
    }

    logging.info("Result done")
    return result_dict, str(batch_expiry_bool)


if __name__ == '__main__':
    image_p = './rotate/01.jpg'
    # image_p = 'output_image.png'
    image = cv2.imread(image_p)
    print(json.dumps(po_vision_main(image), indent=4, ensure_ascii=False))



