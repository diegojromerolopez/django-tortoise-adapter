import json
import time
import unittest
import urllib.parse
import urllib.request

BASE_URL = "http://web:8000"


class TestPollsE2E(unittest.TestCase):
    unique_suffix: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.unique_suffix = str(int(time.time()))

    def test_1_create_and_list_question(self) -> None:
        # Create
        question_text = f"Question {self.unique_suffix}"
        payload = json.dumps({"question_text": question_text}).encode()
        req = urllib.request.Request(f"{BASE_URL}/create/", data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertEqual(data["question_text"], question_text)

        # List
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertIn(question_text, data["questions"])

    def test_2_create_choice(self) -> None:
        # First ensure a question exists to attach a choice, grab its ID
        question_text = f"Choice Question {self.unique_suffix}"
        payload = json.dumps({"question_text": question_text}).encode()
        req = urllib.request.Request(f"{BASE_URL}/create/", data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            q_id = data["id"]

        req = urllib.request.Request(f"{BASE_URL}/{q_id}/choice/create/", method="POST")
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertEqual(data["choice_text"], "Not much")

    def test_3_get_question(self) -> None:
        # We'll use the question from test_1
        question_text = f"Question {self.unique_suffix}"
        encoded_text = urllib.parse.quote(question_text)
        req = urllib.request.Request(f"{BASE_URL}/get/{encoded_text}/")
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read().decode())
            self.assertEqual(data["question_text"], question_text)


if __name__ == "__main__":
    unittest.main()
