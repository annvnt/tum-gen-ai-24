import base64
from mistralai import Mistral, OCRResponse


def encode_pdf(pdf_path):
    """Encode the pdf to base64."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {pdf_path} was not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def mistral_ocr(pdf_path: str) -> OCRResponse:
    """
    :param pdf_path: path to the pdf file
    """
    # Getting the base64 string
    base64_pdf = encode_pdf(pdf_path)

    client = Mistral(api_key="6qNM0lyL5udlkZL7sqEwLVcGYE77JPEV")

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{base64_pdf}"
        },
        include_image_base64=True
    )

    return ocr_response


if __name__ == '__main__':
    print(mistral_ocr("Report & Financials Statements 2024.pdf"))
