import argparse
import os
import pathlib

eu4_escape_targets = [
    ord("¤"),
    ord("£"),
    ord("§"),
    ord("$"),
    ord("["),
    ord("]"),
    0x00,  # null character
    ord("\\"),
    ord(" "),
    0x0D,  # 改行
    0x0A,  # 改行
    ord("\""),
    ord("/"),
    ord("{"),
    ord("}"),
    ord("@"),
    ord(";"),
    0x80,
    0x7E,
    ord("½"),
    ord("_"),
    ord("#")  # ymlのコメント
]

ck2_escape_targets = [
    0xA4,
    0xA3,
    0xA7,
    0x24,
    0x5B,
    0x00,
    0x5C,
    0x20,
    0x0D,
    0x0A,
    0x22,
    0x7B,
    0x7D,
    0x40,
    0x3B,
    0x80,
    0x7E,
    0xBD,
    0x5F
]


def generate_encoder(game_type, ext):
    """

    :param game_type: ゲーム種別
    :param ext: 拡張子
    :return:
    """

    # 定義
    if game_type == "eu4":
        escape_targets = eu4_escape_targets
        high_byte_shift = -9
        low_byte_shift = 14
    elif game_type == "ck2":
        escape_targets = ck2_escape_targets
        high_byte_shift = -9
        low_byte_shift = 15
    else:
        raise Exception("typeが不明")

    def ___(src_array):
        return __(map(ucs_to_cp1252, src_array))

    def ____(src_array):
        return map(cp1252_to_ucs2, __(src_array))

    def __(src_array):
        """
        変換器
        :param src_array: コードポイント配列
        :return:
        """
        result = []
        for code_point in src_array:

            # BMP外の文字
            if code_point > 0xFFFF:
                print("not convert character")
                continue

            # null文字
            if code_point == 0:
                print("Found null character")
                continue

            high_byte = (code_point >> 8) & 0x000000FF
            low_byte = code_point & 0x000000FF

            # 2byteじゃない
            if high_byte == 0:
                result.append(code_point)
                continue

            escape_char = 0x10

            if high_byte in escape_targets:
                escape_char += 2

            if low_byte in escape_targets:
                escape_char += 1

            if escape_char == 0x11:
                low_byte = low_byte + low_byte_shift
            elif escape_char == 0x12:
                high_byte = high_byte + high_byte_shift
            elif escape_char == 0x13:
                low_byte = low_byte + low_byte_shift
                high_byte = high_byte + high_byte_shift
            else:
                pass

            result.append(escape_char)
            result.append(low_byte)
            result.append(high_byte)

        return result

    if game_type == "eu4":
        if ext == "yml":
            return ____
        elif ext == "txt":
            return ___
        else:
            raise Exception()

    elif game_type == "ck2":
        if ext in ["csv", "txt"]:
            return ___
        else:
            raise Exception()
    else:
        raise Exception()


ucs2_to_cp1252_table = {
    0x20AC: 0x80,  # €
    # 0x81
    0x201A: 0x82,  # ‚
    0x0192: 0x83,  # ƒ
    0x201E: 0x84,  # „
    0x2026: 0x85,  # …
    0x2020: 0x86,  # †
    0x2021: 0x87,  # ‡
    0x02C6: 0x88,  # ˆ
    0x2030: 0x89,  # ‰
    0x0160: 0x8A,  # Š
    0x2039: 0x8B,  # ‹
    0x0152: 0x8C,  # Œ
    # 0x8D
    0x017D: 0x8E,  # Ž
    # 0x8F
    # 0x90
    0x2018: 0x91,  # ‘
    0x2019: 0x92,  # ’
    0x201C: 0x93,  # “
    0x201D: 0x94,  # ”
    0x2022: 0x95,  # •
    0x2013: 0x96,  # –
    0x2014: 0x97,  # —
    0x02DC: 0x98,  # ˜
    0x2122: 0x99,  # ™
    0x0161: 0x9A,  # š
    0x203A: 0x9B,  # ›
    0x0153: 0x9C,  # œ
    # 0x9D
    0x017E: 0x9E,  # ž
    0x0178: 0x9F  # Ÿ
}

cp1252_to_ucs2_table = {
    0x80: 0x20AC,  # €
    # 0x81
    0x82: 0x201A,  # ‚
    0x83: 0x0192,  # ƒ
    0x84: 0x201E,  # „
    0x85: 0x2026,  # …
    0x86: 0x2020,  # †
    0x87: 0x2021,  # ‡
    0x88: 0x02C6,  # ˆ
    0x89: 0x2030,  # ‰
    0x8A: 0x0160,  # Š
    0x8B: 0x2039,  # ‹
    0x8C: 0x0152,  # Œ
    # 0x8D
    0x8E: 0x017D,  # Ž
    # 0x8F
    # 0x90
    0x91: 0x2018,  # ‘
    0x92: 0x2019,  # ’
    0x93: 0x201C,  # “
    0x94: 0x201D,  # ”
    0x95: 0x2022,  # •
    0x96: 0x2013,  # –
    0x97: 0x2014,  # —
    0x98: 0x02DC,  # ˜
    0x99: 0x2122,  # ™
    0x9A: 0x0161,  # š
    0x9B: 0x203A,  # ›
    0x9C: 0x0153,  # œ
    # 0x9D
    0x9E: 0x017E,  # ž
    0x9F: 0x0178  # Ÿ
}


def ucs_to_cp1252(code_point):
    if code_point in ucs2_to_cp1252_table:
        return ucs2_to_cp1252_table[code_point]
    else:
        return code_point


def cp1252_to_ucs2(code_point):
    if code_point in cp1252_to_ucs2_table:
        return cp1252_to_ucs2_table[code_point]
    else:
        return code_point


def generate_printer(game_type, ext):
    """
    プリンター生成器
    :param game_type: ゲーム種別
    :param ext: 拡張子
    :return: プリンター
    """

    def utf8_printer(src_array, out_file_path):
        with open(out_file_path, "wt", encoding="utf_8_sig") as fw:
            text = "".join(map(chr, src_array))
            fw.write(text)

    def cp1252_like_printer(src_array, out_file_path):
        """
        純粋にCP1252ではない。（規定されていない0x81や0x90などのコードポイントも出現しうる）、
        バイナリモードで書き込む
        :param src_array:
        :param out_file_path:
        :return:
        """

        w = bytearray(map(ucs_to_cp1252, src_array))

        with open(out_file_path, "wb") as fw:
            fw.write(w)

    if game_type == "eu4":
        if ext == "yml":
            return utf8_printer
        elif ext == "txt":
            return cp1252_like_printer
        else:
            raise Exception()

    elif game_type == "ck2":
        if ext in ["csv", "txt"]:
            return cp1252_like_printer
        else:
            raise Exception()
    else:
        raise Exception()


def target_is_directory(params):
    is_out_dir = os.path.isdir(str(params.out))

    # 走査
    for file_path in pathlib.Path(params.src).glob('**/*.*'):
        if file_path.suffix not in ['.yml', '.csv', '.txt']:
            continue

        # 指定がない場合は、ソースと同じ場所に、同じ名前で拡張子を.encodedにしたものを保存する
        if params.out is None:
            out_file_path = os.path.join(
                os.path.dirname(os.path.abspath(str(file_path))),
                os.path.basename(str(file_path)) + ".encode"
            )

        # 出力先が存在するディレクトリ
        elif is_out_dir:
            out_file_path = os.path.join(
                str(params.out),
                str(file_path).replace(str(params.src) + "\\", "")
            )

            dir_path = os.path.dirname(str(out_file_path))
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        else:
            raise Exception("出力先が不正")

        do_file(in_file_path=file_path,
                out_file_path=out_file_path,
                encoder=generate_encoder(params.type, os.path.splitext(str(file_path))[1][1:]),
                printer=generate_printer(params.type, os.path.splitext(str(file_path))[1][1:]),
                is_bom=params.bom)


def target_is_file(params):
    # 指定がない場合は、ソースと同じ場所に、同じ名前で拡張子を.utf8にしたものを保存する
    if params.out is None:
        out_file_path = os.path.join(
            os.path.dirname(os.path.abspath(params.src)),
            os.path.basename(params.src) + ".encode"
        )

    # 指定先が存在するディレクトリの場合は、そこに同じ名前で保存する
    elif os.path.isdir(params.out):
        out_file_path = os.path.join(
            params.out,
            os.path.basename(params.src)
        )

    # 指定先がフルパス
    elif params.out != "":
        out_file_path = params.out
    else:
        raise Exception("出力先が不正")

    do_file(in_file_path=params.src,
            out_file_path=out_file_path,
            encoder=generate_encoder(params.type, os.path.splitext(str(params.src))[1][1:]),
            printer=generate_printer(params.type, os.path.splitext(str(params.src))[1][1:]),
            is_bom=params.bom)


def do_file(in_file_path, out_file_path, encoder, printer, is_bom):
    """
    ファイルを変換
    :param in_file_path: 入力先ファイルパス
    :param out_file_path: 出力先ファイルパス
    :param encoder: エンコーダー
    :param printer: プリンター
    :param is_bom : bom付きかどうか
    :return:
    """

    if is_bom:
        encoding = 'utf_8_sig'
    else:
        encoding = 'utf_8'

    # 読み込み
    with open(in_file_path, "rt", encoding=encoding) as fr:
        printer(src_array=encoder(src_array=map(ord, fr.read())),
                out_file_path=out_file_path)


def generate_default_arg_parser():
    """
    argumentsパーサーを作成
    :return: パーサー
    """

    # title
    result = argparse.ArgumentParser(
        description='Process some integers.'
    )

    # ソース
    result.add_argument(
        'src',
        metavar='src',
        type=str,
        help='source file or directory.')

    # 出力先
    result.add_argument(
        '-out',
        metavar='X',
        dest='out',
        help='output directory')

    # タイプ
    result.add_argument(
        '-type',
        metavar='X',
        dest='type',
        default="eu4",
        help='eu4 or ck2')

    # bomがある
    result.add_argument(
        '--bom',
        action='store_true',
        dest='bom',
        help='utf8 with bom')

    return result


def special_escape(arg_params):
    """
    main
    :return:
    """

    # fileかdirか
    if os.path.isfile(arg_params.src):
        target_is_file(params=arg_params)
    elif os.path.isdir(arg_params.src):
        target_is_directory(params=arg_params)
    else:
        raise Exception("srcがみつからない")


if __name__ == '__main__':
    """
    entry-point
    """
    parser = generate_default_arg_parser()
    params = parser.parse_args()

    special_escape(arg_params=params)
