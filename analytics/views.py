import requests   # used to call external API

from django.utils import timezone # it will give time in UTC but datetime will not
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CPProfile

from datetime import datetime  # convert timestamp
from .models import Submission

class FetchCFProfile(APIView):
    permission_classes = [IsAuthenticated]  # require login

    
    def post(self, request):
        user = request.user   # current logged-in user
        handle = request.user.cf_handle
        
        url = f"https://codeforces.com/api/user.info?handles={handle}"  
        # CF API endpoint

        res = requests.get(url).json()  # call API + convert to JSON

        if res['status'] != 'OK':
            return Response({"error": "Invalid handle"}, status=400)
        
        data = res['result'][0]  # extract user data
        
        profile, _ = CPProfile.objects.get_or_create(user=user)  
        # get existing or create new
        
        profile.cf_handle = handle
        profile.rating = data.get('rating')  # safe access
        profile.max_rating = data.get('maxRating')
        profile.save()  # save to DB

        
        return Response({
            "rating": profile.rating,
            "max_rating": profile.max_rating
        })
 
class FetchCFSubmissions(APIView):
    permission_classes = [IsAuthenticated]  # only logged-in users

    
    def post(self, request):
        user = request.user  # current user
        
        handle = request.user.cf_handle
        
        url = f"https://codeforces.com/api/user.status?handle={handle}"  
        # CF submissions API
        
        res = requests.get(url).json()  # call API
        
        if res['status'] != 'OK':
            return Response({"error": "Failed to fetch"}, status=400)
        
        submissions = res['result']  # list of submissions
        
        Submission.objects.filter(user=user).delete()  
        # delete old data → avoid duplicates
        
        # limit to 200 (performance safe)
        for sub in submissions[:200]:  
            problem = sub.get('problem', {})  # problem info

            Submission.objects.create(
                user=user,
                problem_name=problem.get('name'),  # title
                verdict=sub.get('verdict'),  # OK / WA
                tags=problem.get('tags', []),  # list of tags
                rating=problem.get('rating'),  # difficulty
                creation_time=datetime.fromtimestamp(sub.get('creationTimeSeconds'))
            )
            
        return Response({"msg": "Submissions stored"})

from collections import defaultdict  # auto-initialize dict

class TopicAnalysis(APIView):
    permission_classes = [IsAuthenticated]  # login required

    def get(self, request):
        user = request.user  # current user
        
        submissions = Submission.objects.filter(user=user)  
        # get all submissions of user
        
        topic_data = defaultdict(lambda: {"total": 0, "correct": 0, "last_solved" : None})
        # structure:
        # {
        #   "dp": {"total": 10, "correct": 5}
        # }
        
        for sub in submissions:
            tags = sub.tags  # list of tags
            
            for tag in tags:
                topic_data[tag]["total"] += 1  # count attempt
                
                if sub.verdict == "OK":
                    topic_data[tag]["correct"] += 1  # count success
                    
        result = {}
        
        for tag, data in topic_data.items():
            total = data["total"]
            correct = data["correct"]
            
            accuracy = (correct / total) * 100 if total > 0 else 0
            # avoid division by zero
            
            result[tag] = {
                "total_submissions": total,
                "correct_submissions": correct,
                "accuracy": round(accuracy, 2)
            }
            
        return Response(result)
    
class Weak_and_Strong_Topics(APIView):
    permission_classes = [IsAuthenticated]  # login required

    def get(self, request):
        user = request.user  # current user
        
        submissions = Submission.objects.filter(user=user)  
        # get all submissions
        
        topic_data = defaultdict(lambda: {"total": 0, "correct": 0, "last_solved" : None})
        
        for sub in submissions:
            for tag in sub.tags:
                topic_data[tag]["total"] += 1
                if sub.verdict == "OK":
                    topic_data[tag]["correct"] += 1
                    # track latest correct submission time
                    if (topic_data[tag]["last_solved"] is None or
                        sub.creation_time > topic_data[tag]["last_solved"]):
                        topic_data[tag]["last_solved"] = sub.creation_time
                    
        weak_topics = []
        strong_topics = []
        
        now = timezone.now()  # current time
        
        for tag, data in topic_data.items():
            total = data["total"]
            correct = data["correct"]
            accuracy = (correct / total) * 100 if total > 0 else 0
            last_solved = data["last_solved"]
            
            days_gap = (now - last_solved).days if last_solved else 999  
            # if never solved → treat as very old
            
            
            is_weak = False
            if total >= 5 and accuracy < 40:
                is_weak = True  # poor accuracy
                
            if total > 20 and accuracy < 60:
                is_weak = True  # many attempts but still weak
                
            topic_info = {
                "tag": tag,
                "accuracy": round(accuracy, 2),
                "total_submissions": total,
                "last_solved_days_ago": days_gap
            }
            
            if is_weak:
                weak_topics.append(topic_info)
            else:
                strong_topics.append(topic_info)
                
        weak_topics.sort(key=lambda x: x["accuracy"])  
        # lowest accuracy first
        strong_topics.sort(key=lambda x: -x["accuracy"])
        # highest accuracy first
        
        return Response({
            "weak_topics": weak_topics,
            "strong_topics": strong_topics
        })
        
class RatingAnalysis(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        submissions = Submission.objects.filter(user=user)

        rating_data = defaultdict(lambda: {"total": 0, "correct": 0})

        for sub in submissions:
            if sub.rating is None:
                continue  # skip if no rating

            # create bucket (e.g., 800-1000, 1000-1200)
            bucket = (sub.rating // 200) * 200
            key = f"{bucket}-{bucket + 200}"

            rating_data[key]["total"] += 1

            if sub.verdict == "OK":
                rating_data[key]["correct"] += 1

        result = {}

        for bucket, data in rating_data.items():
            total = data["total"]
            correct = data["correct"]

            accuracy = (correct / total) * 100 if total > 0 else 0

            result[bucket] = {
                "total_submissions": total,
                "correct_submissions": correct,
                "accuracy": round(accuracy, 2)
            }

        sorted_result = dict(sorted(result.items(), key=lambda x: int(x[0].split('-')[0])))

        return Response(sorted_result)

class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        submissions = Submission.objects.filter(user=user)

        # -------------------------------
        # STEP 1: Topic Analysis
        # -------------------------------
        topic_data = defaultdict(lambda: {
            "total": 0,
            "correct": 0,
            "last_solved": None
        })

        for sub in submissions:
            for tag in sub.tags:
                topic_data[tag]["total"] += 1

                if sub.verdict == "OK":
                    topic_data[tag]["correct"] += 1

                    if (topic_data[tag]["last_solved"] is None or
                        sub.creation_time > topic_data[tag]["last_solved"]):
                        topic_data[tag]["last_solved"] = sub.creation_time

        weak_topics = []
        strong_topics = []

        now = timezone.now()

        for tag, data in topic_data.items():
            total = data["total"]
            correct = data["correct"]

            accuracy = (correct / total) * 100 if total > 0 else 0
            last_solved = data["last_solved"]

            days_gap = (now - last_solved).days if last_solved else 999

            is_weak = False

            if total >= 5 and accuracy < 40:
                is_weak = True
            if total > 20 and accuracy < 60:
                is_weak = True

            if is_weak:
                weak_topics.append(tag)
            else:
                strong_topics.append(tag)

        # -------------------------------
        # STEP 2: Rating Analysis
        # -------------------------------
        rating_data = defaultdict(lambda: {"total": 0, "correct": 0})

        for sub in submissions:
            if sub.rating is None:
                continue

            bucket_start = (sub.rating // 200) * 200
            bucket = f"{bucket_start}-{bucket_start + 200}"

            rating_data[bucket]["total"] += 1

            if sub.verdict == "OK":
                rating_data[bucket]["correct"] += 1

        # Sort rating buckets
        sorted_ratings = sorted(
            rating_data.items(),
            key=lambda x: int(x[0].split('-')[0])
        )

        # -------------------------------
        # STEP 3: Find Comfort Rating
        # -------------------------------
        MIN_ATTEMPTS = 15
        comfort_rating = None

        for bucket, data in sorted_ratings:
            total = data["total"]
            correct = data["correct"]

            if total < MIN_ATTEMPTS:
                continue  # skip unreliable buckets

            accuracy = (correct / total) * 100 if total > 0 else 0

            if accuracy >= 50:
                comfort_rating = bucket

        # fallback logic
        if comfort_rating is None and sorted_ratings:
            # try lowest bucket with enough attempts
            for bucket, data in sorted_ratings:
                if data["total"] >= MIN_ATTEMPTS:
                    comfort_rating = bucket
                    break

            # if still none → fallback to lowest bucket
            if comfort_rating is None:
                comfort_rating = sorted_ratings[0][0]

        # -------------------------------
        # STEP 4: Find Next Rating
        # -------------------------------
        next_rating = None

        if comfort_rating:
            start = int(comfort_rating.split('-')[0])
            next_rating = f"{start + 200}-{start + 400}"

        # -------------------------------
        # STEP 5: Generate Recommendations
        # -------------------------------
        recommendations = []

        # Weak topics → practice at comfort level
        for topic in weak_topics[:3]:
            if comfort_rating:
                recommendations.append(
                    f"Practice {topic} problems in rating range {comfort_rating}"
                )

        # Strong topics → push to next level
        for topic in strong_topics[:2]:
            if next_rating:
                recommendations.append(
                    f"Try harder {topic} problems in rating range {next_rating}"
                )

        # Inactive topics → revision
        for tag, data in topic_data.items():
            last_solved = data["last_solved"]
            days_gap = (now - last_solved).days if last_solved else 999

            if days_gap > 30:
                recommendations.append(
                    f"Revise {tag}, you haven't practiced it recently, You can start with rating in range of {comfort_rating}"
                )

        # Remove duplicates
        recommendations = list(set(recommendations))

        # Limit output
        recommendations = recommendations[:6]

        return Response({
            "comfort_rating": comfort_rating,
            "next_target_rating": next_rating,
            "recommendations": recommendations
        })
