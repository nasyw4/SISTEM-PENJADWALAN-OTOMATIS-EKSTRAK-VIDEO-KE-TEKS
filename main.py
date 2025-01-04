# -*- coding: utf-8 -*-
"""Streamlit - Auto Scheduling & Video to  Text Conversion

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1d743hUhpfjJEfTKx4poNGA2rATRhKO8z

## Install Library
"""
# Install library yang diperlukan
# !pip install git+https://github.com/openai/whisper.git
# !pip install torch moviepy soundfile
# !pip install gradio
# !pip install streamlit

import os
import streamlit as st
import os
import random
import matplotlib.pyplot as plt
import whisper
from moviepy.editor import VideoFileClip
from matplotlib import pyplot as plt
from io import BytesIO

# Setup for the directories
os.makedirs('temp', exist_ok=True)
os.makedirs('output', exist_ok=True)

"""## Ekstraksi Audio from Video"""

class Admin:
    def uploadVideo(self, video_path):
        """Upload and process a video file"""
        video = Video(video_path)
        if video.validateFormat():
            return video
        return None

    def viewTranscription(self, transcription):
        """View the transcription content"""
        return transcription.display()

    def downloadTranscription(self, transcription):
        """Download the transcription file"""
        return transcription.download()

class Video:
    def __init__(self, video_path):
        self.videoId = str(hash(video_path))
        self.filename = os.path.basename(video_path)
        self.format = os.path.splitext(video_path)[1]
        self.video_path = video_path

    def validateFormat(self):
        """Validate if the video format is supported"""
        valid_formats = ['.mp4', '.avi', '.mov', '.mkv']
        return self.format.lower() in valid_formats

    def extractAudio(self):
        """Extract audio from video file"""
        try:
            # Create output directory if it doesn't exist
            audio_path = os.path.join('temp', f"temp_audio_{self.videoId}.wav")
            video = VideoFileClip(self.video_path)
            video.audio.write_audiofile(audio_path)
            video.close()
            return Audio(audio_path, self.videoId)
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return None

class Audio:
    def __init__(self, audio_path, video_id):
        self.audioId = f"audio_{video_id}"
        self.audio_path = audio_path

    def convertToText(self):
        """Convert audio to text using Whisper"""
        try:
            model = whisper.load_model("base")
            result = model.transcribe(self.audio_path, language="Indonesian")
            # Clean up temporary audio file
            os.remove(self.audio_path)
            return Transcription(result["text"], self.audioId)
        except Exception as e:
            print(f"Error converting to text: {e}")
            return None

class Transcription:
    def __init__(self, content, audio_id):
        self.transcriptionId = f"trans_{audio_id}"
        self.content = content

        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        self.filename = os.path.join('output', f"transcription_{self.transcriptionId}.txt")

    def display(self):
        """Display transcription content"""
        return self.content

    def download(self):
        """Save and return transcription file"""
        try:
            with open(self.filename, "w", encoding='utf-8') as f:
                f.write(self.content)
            return self.filename
        except Exception as e:
            print(f"Error saving transcription: {e}")
            return None

"""## Auto Scheduling

"""

class Individu:
    def __init__(self, kromosom, score=0):
        self.kromosom = kromosom
        self.score = score

    def setScore(self, score):
        self.score = score

class Scheduler:
    def __init__(self, guru_list, kelas_list, pelajaran_list, hari_list, jumlah_slot):
        self.guru_list = guru_list
        self.kelas_list = kelas_list
        self.pelajaran_list = pelajaran_list
        self.hari_list = hari_list
        self.jumlah_slot = jumlah_slot
        self.target_teachings_per_teacher = 9  # Target mengajar untuk setiap guru

    def calculate_daily_teacher_load(self, kromosom, hari):
        teacher_load = {guru: 0 for guru in self.guru_list}
        for kelas in self.kelas_list:
            for slot in range(self.jumlah_slot):
                if slot != 2 and kromosom[hari][kelas][slot] != "":
                    guru = kromosom[hari][kelas][slot][0]
                    teacher_load[guru] += 1
        return teacher_load

    def generate_kromosom(self):
        kromosom = {}
        teacher_total_load = {guru: 0 for guru in self.guru_list}

        for hari in self.hari_list:
            kromosom_harian = {}
            for kelas in self.kelas_list:
                jadwal_kelas = [""] * self.jumlah_slot
                jadwal_kelas[2] = "Istirahat" # Slot untuk istirahat
                kromosom_harian[kelas] = jadwal_kelas # 4 slot untuk setiap kelas

            # Distribusi guru agar lebih merata
            for kelas in self.kelas_list:
                available_slots = [0, 1, 3]
                random.shuffle(available_slots)

                for slot in available_slots[:2]: # 2 mata pelajaran dalam 1 hari
                    # Mengurutkan guru berdasarkan beban kerja saat ini
                    sorted_teachers = sorted(self.guru_list, key=lambda x: teacher_total_load[x])

                    # Menugaskan guru dengan beban kerja terendah saat ini
                    for guru in sorted_teachers:
                        if teacher_total_load[guru] < self.target_teachings_per_teacher: # Assign guru kedalam slot jika kondisi guru mengajar < target
                            pelajaran = self.pelajaran_list[self.guru_list.index(guru)]
                            kromosom_harian[kelas][slot] = (guru, pelajaran)
                            teacher_total_load[guru] += 1
                            break

            kromosom[hari] = kromosom_harian
        return kromosom

    def fitness_function(self, individu):
        score = 0
        teacher_distribution = {guru: 0 for guru in self.guru_list}
        conflicts = 0

        # Periksa distribusi guru dan konflik
        for hari in self.hari_list:
            daily_teacher_slots = {slot: [] for slot in range(self.jumlah_slot) if slot != 2}

            for kelas in self.kelas_list:
                for slot in daily_teacher_slots.keys():
                    if individu.kromosom[hari][kelas][slot] != "":
                        guru = individu.kromosom[hari][kelas][slot][0]
                        daily_teacher_slots[slot].append(guru)
                        teacher_distribution[guru] += 1

            # Hitung konflik guru dalam 1 slot dan berikan penalti
            for slot_teachers in daily_teacher_slots.values():
                for guru in set(slot_teachers):
                    if slot_teachers.count(guru) > 1:
                        conflicts += (slot_teachers.count(guru) - 1) * 50  # Penalti yang lebih berat

        # Skor berdasarkan distribusi guru
        for count in teacher_distribution.values():
            if count == self.target_teachings_per_teacher: # Jika guru mengajar sesuai dengan target yang telah ditentukan maka berikan point +
                score += 20
            else:
                score -= abs(count - self.target_teachings_per_teacher) * 5 # Menghitung selisih guru dan target mengajar

        # Penalti untuk konflik
        score -= conflicts # SKor penalti untuk distribusi guru yang tidak seimbang (terdapat indikasi konflik)

        # Bonus untuk distribusi harian yang seimbang
        for hari in self.hari_list:
            daily_load = self.calculate_daily_teacher_load(individu.kromosom, hari)
            max_daily = max(daily_load.values())
            min_daily = min(daily_load.values())
            if max_daily - min_daily <= 1:
                score += 10

        individu.setScore(score)
        return score

class Optimize:
    def __init__(self, population_size, generations, mutation_rate, scheduler):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.scheduler = scheduler

    def pick_one(self, population):
        total_score = sum(ind.score for ind in population)
        pick = random.uniform(0, total_score)
        current = 0
        for ind in population:
            current += ind.score
            if current > pick:
                return ind
        return population[-1]

    def evolve_population(self, population):
        new_population = []
        for _ in range(len(population)):
            parentA = self.pick_one(population)
            parentB = self.pick_one(population)
            child = self.crossover(parentA, parentB)
            self.mutate(child)
            new_population.append(child)

        for individu in new_population:
            self.scheduler.fitness_function(individu)

        return new_population

    def crossover(self, parentA, parentB):
        child_kromosom = {}
        for hari in self.scheduler.hari_list:
            child_kromosom_harian = {}
            for kelas in self.scheduler.kelas_list:
                if random.random() < 0.5:
                    child_kromosom_harian[kelas] = parentA.kromosom[hari][kelas]
                else:
                    child_kromosom_harian[kelas] = parentB.kromosom[hari][kelas]
            child_kromosom[hari] = child_kromosom_harian

        child = Individu(child_kromosom)
        return child

    def mutate(self, individu):
        for hari in self.scheduler.hari_list:
            for kelas in self.scheduler.kelas_list:
                if random.random() < self.mutation_rate:
                    individu.kromosom[hari][kelas] = [""] * self.scheduler.jumlah_slot
                    individu.kromosom[hari][kelas][2] = "Istirahat"
                    subjects_assigned = random.sample(self.scheduler.pelajaran_list, 2)
                    slots_filled = random.sample([0, 1, 3], 2)
                    available_teachers = self.scheduler.guru_list[:]

                    for slot, pelajaran in zip(slots_filled, subjects_assigned):
                        possible_teachers = [g for g, p in zip(self.scheduler.guru_list, self.scheduler.pelajaran_list) if p == pelajaran and g in available_teachers]
                        if possible_teachers:
                            guru = possible_teachers[0]
                            individu.kromosom[hari][kelas][slot] = (guru, pelajaran)
                            available_teachers.remove(guru)

        self.scheduler.fitness_function(individu)

    def run(self):
        population = [Individu(self.scheduler.generate_kromosom()) for _ in range(self.population_size)]
        for individu in population:
            self.scheduler.fitness_function(individu)

        best_individu = max(population, key=lambda x: x.score)

        for generation in range(1, self.generations + 1):
            population = self.evolve_population(population)
            for individu in population:
                self.scheduler.fitness_function(individu)

            current_best = max(population, key=lambda x: x.score)

            if current_best.score > best_individu.score:
                best_individu = current_best

        return best_individu

class Manage:
    def __init__(self, guru_list, kelas_list, pelajaran_list, hari_list, jumlah_slot):
        self.guru_list = guru_list
        self.kelas_list = kelas_list
        self.pelajaran_list = pelajaran_list
        self.hari_list = hari_list
        self.jumlah_slot = jumlah_slot
        self.scheduler = Scheduler(guru_list, kelas_list, pelajaran_list, hari_list, jumlah_slot)

    def visualize_schedule(self, individu):
        fig, axes = plt.subplots(len(self.hari_list), len(self.kelas_list), figsize=(20, 15))
        fig.suptitle('Jadwal Sekolah SMP')

        for i, hari in enumerate(self.hari_list):
            for j, kelas in enumerate(self.kelas_list):
                ax = axes[i, j]
                ax.set_title(f'{hari} - {kelas}')
                ax.set_xticks(range(self.jumlah_slot))
                schedule = individu.kromosom[hari][kelas]
                for k, slot in enumerate(schedule):
                    if slot == "Istirahat":
                        ax.barh(k, 1, color='grey')
                    elif slot == "":
                        ax.barh(k, 1, color='white')
                    else:
                        guru, pelajaran = slot
                        color = 'blue'
                        teachers_in_slot = []
                        for kelas2 in self.kelas_list:
                            if individu.kromosom[hari][kelas2][k] not in ["", "Istirahat"]:
                                teachers_in_slot.append(individu.kromosom[hari][kelas2][k][0])
                        if teachers_in_slot.count(guru) > 1:
                            color = 'red'
                        ax.barh(k, 1, color=color)
                        ax.text(0.5, k, f'{guru}\n{pelajaran}', ha='center', va='center', color='white')
                ax.invert_yaxis()

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        return fig

class Main:
    def __init__(self):
        os.makedirs('temp', exist_ok=True)
        os.makedirs('output', exist_ok=True)
        self.build_interface()

    # Fungsi untuk memeriksa apakah input sudah sesuai
    def periksa_input(self, guru_list, kelas_list, pelajaran_list, hari_list, jumlah_slot):
        if not guru_list or not kelas_list or not pelajaran_list or not hari_list:
            return False, "EROR!!! INPUT TIDAK BOLEH KOSONG!"

        for input_list, nama in [(guru_list, "guru"), (kelas_list, "kelas"), (pelajaran_list, "mata pelajaran"), (hari_list, "hari")]:
            if any(not isinstance(item, str) or not item for item in input_list):
                return False, f"EROR!!! INPUT {nama} TIDAK VALID!!!"

        try:
            jumlah_slot = int(jumlah_slot)
            if jumlah_slot <= 0:
                return False, "EROR!!! INPUT TIDAK VALID!!!"
        except ValueError:
            return False, "EROR!!! INPUT TIDAK VALID!!!"

        return True, "INPUT VALID, MENJALANKAN OPTIMASI..."

    # Fungsi untuk menjalankan algoritma dan menampilkan hasil
    def jalankan_algoritma(self, guru_input, kelas_input, pelajaran_input, hari_input, slot_input):
        guru_list = [g.strip() for g in guru_input.split(',') if g.strip()]
        kelas_list = [k.strip() for k in kelas_input.split(',') if k.strip()]
        pelajaran_list = [p.strip() for p in pelajaran_input.split(',') if p.strip()]
        hari_list = [h.strip() for h in hari_input.split(',') if h.strip()]

        manage = Manage(guru_list, kelas_list, pelajaran_list, hari_list, int(slot_input))
        optimize = Optimize(50, 1000, 0.1, manage.scheduler)

        best_individu = optimize.run()
        visualisasi_jadwal = manage.visualize_schedule(best_individu)

        return visualisasi_jadwal

    def process_video_transcription(self, video_path):
        try:
            admin = Admin()

            video = admin.uploadVideo(video_path)
            if not video:
                return "Invalid video format", None

            audio = video.extractAudio()
            if not audio:
                return "Audio extraction failed", None

            transcription = audio.convertToText()
            if not transcription:
                return "Transcription failed", None

            text_content = admin.viewTranscription(transcription)
            file_path = admin.downloadTranscription(transcription)

            return text_content, file_path
        except Exception as e:
            return f"An error occurred: {str(e)}", None

    def build_interface(self):
        st.title("SISTEM PENJADWALAN OTOMATIS & EKSTRAK VIDEO KE TEKS")

        tab1, tab2 = st.tabs(["Penjadwalan", "Ekstrak Video ke Teks"])

        with tab1:
            st.header("Penjadwalan")
            guru_input = st.text_input("Masukan Data Guru : (Pisahkan dengan koma)")
            kelas_input = st.text_input("Masukan Data Kelas : (Pisahkan dengan koma)")
            pelajaran_input = st.text_input("Masukan Data Mata Pelajaran : (Pisahkan dengan koma)")
            hari_input = st.text_input("Masukan Data Hari : (Pisahkan dengan koma)")
            slot_input = st.text_input("Masukan Jumlah Slot : ")

            if st.button("Optimasi"):
                guru_list = [g.strip() for g in guru_input.split(',') if g.strip()]
                kelas_list = [k.strip() for k in kelas_input.split(',') if k.strip()]
                pelajaran_list = [p.strip() for p in pelajaran_input.split(',') if p.strip()]
                hari_list = [h.strip() for h in hari_input.split(',') if h.strip()]

                valid, pesan = self.periksa_input(guru_list, kelas_list, pelajaran_list, hari_list, slot_input)

                st.write(pesan)

                if valid:
                    try:
                        jadwal = self.jalankan_algoritma(guru_input, kelas_input, pelajaran_input, hari_input, slot_input)
                        st.pyplot(jadwal)
                    except Exception as e:
                        st.error(f"Terjadi kesalahan dalam proses optimasi: {str(e)}")

        with tab2:
            st.header("Ekstrak Video ke Teks")
            video_file = st.file_uploader("Upload Video", type=["mp4", "avi", "mov"])

            if st.button("Transcribe Video"):
                if video_file:
                    transcription, file_path = self.process_video_transcription(video_file)

                    if transcription:
                        st.text_area("Transcription", transcription, height=200)
                        with open(file_path, "rb") as f:
                            st.download_button("Download Transcription", f, file_name="transcription.txt")
                    else:
                        st.error("Terjadi kesalahan dalam transkripsi video.")
                else:
                    st.warning("Silakan unggah file video terlebih dahulu.")

if __name__ == "__main__":
    Main()

# if __name__ == "__main__":
#     app = Main()
#     app.launch()