import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from transnova_core import TranslationRequest, extract_translation, request_translation


class TranslationContractTests(unittest.TestCase):
    def test_request_strips_text_and_accepts_context(self):
        item = TranslationRequest(text="  Hello  ", target_language="or", language_name="Odia", context="Engineering")
        self.assertEqual(item.text, "Hello")
        self.assertEqual(item.context, "Engineering")

    def test_request_rejects_blank_text(self):
        with self.assertRaises(ValidationError):
            TranslationRequest(text="   ", target_language="or", language_name="Odia")

    def test_request_rejects_text_over_limit(self):
        with self.assertRaises(ValidationError):
            TranslationRequest(text="x" * 20_001, target_language="or", language_name="Odia")


class ResponseNormalizationTests(unittest.TestCase):
    def test_reads_n8n_list_response(self):
        self.assertEqual(extract_translation([{ "output": "  ନମସ୍କାର  " }]), "ନମସ୍କାର")

    def test_reads_nested_translation_response(self):
        self.assertEqual(extract_translation({"data": {"translation": "Bonjour"}}), "Bonjour")

    def test_rejects_empty_or_invalid_response(self):
        with self.assertRaises(ValueError):
            extract_translation([])
        with self.assertRaises(ValueError):
            extract_translation({"status": "ok"})

    @patch("transnova_core.requests.post")
    def test_webhook_request_validates_and_normalizes(self, post):
        response = Mock()
        response.json.return_value = [{"output": "Hola"}]
        response.raise_for_status.return_value = None
        post.return_value = response
        request = TranslationRequest(text="Hello", target_language="es", language_name="Spanish")
        result = request_translation(request, "https://example.invalid/webhook/transnova-translate")
        self.assertEqual(result.translation, "Hola")
        self.assertEqual(result.character_count, 4)
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 60))


if __name__ == "__main__":
    unittest.main()
