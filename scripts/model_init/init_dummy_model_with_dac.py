from parler_tts import ParlerTTSForCausalLM, ParlerTTSForConditionalGeneration, ParlerTTSDecoderConfig
from transformers import AutoConfig
import os
TMP_DIR = "./tmp/artefacts/"

text_model = "google-t5/t5-small"
encodec_version = "ylacombe/dac_44khZ_8kbps"
num_codebooks = 9

t5 = AutoConfig.from_pretrained(text_model)
encodec = AutoConfig.from_pretrained(encodec_version)

encodec_vocab_size = encodec.codebook_size


decoder_config = ParlerTTSDecoderConfig(
    vocab_size=encodec_vocab_size + 1,
    max_position_embeddings=2048,
    num_hidden_layers=4,
    ffn_dim=512,
    num_attention_heads=8,
    layerdrop=0.0,
    use_cache=True,
    activation_function="gelu",
    hidden_size=512,
    dropout=0.0,
    attention_dropout=0.0,
    activation_dropout=0.0,
    pad_token_id=encodec_vocab_size,
    eos_token_id=encodec_vocab_size,
    bos_token_id=encodec_vocab_size + 1,
    num_codebooks=num_codebooks,
)


decoder = ParlerTTSForCausalLM(decoder_config)
decoder.save_pretrained(os.path.join(TMP_DIR, "decoder"))


model = ParlerTTSForConditionalGeneration.from_sub_models_pretrained(
    text_encoder_pretrained_model_name_or_path=text_model,
    audio_encoder_pretrained_model_name_or_path=encodec_version,
    decoder_pretrained_model_name_or_path=os.path.join(TMP_DIR, "decoder"),
    vocab_size=t5.vocab_size,
)

# set the appropriate bos/pad token ids
model.generation_config.decoder_start_token_id = encodec_vocab_size + 1
model.generation_config.pad_token_id = encodec_vocab_size
model.generation_config.eos_token_id = encodec_vocab_size

# set other default generation config params
model.generation_config.max_length = int(30 * model.audio_encoder.config.frame_rate)
model.generation_config.do_sample = True  # True
model.generation_config.guidance_scale = 1  # 3.0

model.save_pretrained(os.path.join(TMP_DIR, "tiny-model"))