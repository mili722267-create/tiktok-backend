class TikTokRecommendationEngine:
    def __init__(self, user_history):
        """
        የተጠቃሚውን የቪዲዮ ማየት ታሪክ እና ምርጫ ይቀበላል
        """
        self.user_history = user_history

    def calculate_video_score(self, video_metadata):
        """
        አንድን ቪዲዮ ተጠቃሚው ሊወደው የሚችልበትን ደረጃ በነጥብ ያሰላል
        """
        score = 0.0
        
        # 1. ቪዲዮውን ያየበትን ቆይታ መመዘን (ዋናው መለኪያ)
        watch_ratio = self.user_history.get('watch_percentage', 0.0)
        if watch_ratio >= 0.80:
            score += 10.0  # ቪዲዮውን ጨርሶታል ወይም ደጋግሞታል
        elif watch_ratio <= 0.15:
            score -= 5.0   # ወዲያውኑ ወደ ሌላ ቪዲዮ አልፏል (Skip)
            
        # 2. የተጠቃሚውን ቀጥታ ምላሽ መመዘን
        if self.user_history.get('liked', False):
            score += 5.0
        if self.user_history.get('shared', False):
            score += 7.0
            
        # 3. የሃሽታግ ወይም የታግ ተመሳሳይነት መመዘን
        user_favorite_tags = self.user_history.get('favorite_tags', [])
        video_tags = video_metadata.get('tags', [])
        
        # የጋራ ታጎችን መለየት
        common_tags = set(user_favorite_tags) & set(video_tags)
        score += len(common_tags) * 2.0
        
        return score

    def rank_videos(self, all_videos):
        """
        ሁሉንም ቪዲዮዎች በነጥባቸው መሰረት ከከፍተኛ ወደ ዝቅተኛ አደራጅቶ 'For You' ገጽ ላይ ያወጣል
        """
        ranked_list = []
        for video in all_videos:
            video_score = self.calculate_video_score(video)
            video['algorithm_score'] = video_score
            ranked_list.append(video)
            
        # በነጥብ ብዛት መሰረት ከትልቅ ወደ ትንሽ መደርደር (Sorting)
        ranked_list.sort(key=lambda x: x['algorithm_score'], reverse=True)
        return ranked_list
