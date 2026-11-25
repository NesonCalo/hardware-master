# -*- coding: utf-8 -*-
"""把服务条款改成不带地区指向的多语言版本（英文为权威文本），并同步 25 种语言词典与 index.html。"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES = os.path.join(ROOT, "app", "ui", "locales")
INDEX = os.path.join(ROOT, "app", "ui", "index.html")

OLD_NOTE = "本条款提供多语言版本，仅作阅读便利；如译文与简体中文原文有歧义，以简体中文版本为准。"
OLD_W6 = ("本软件按“现状”（AS IS）提供，不附带任何明示或默示的担保，包括但不限于适销性、特定用途适用性与不侵权担保。"
          "在适用法律允许的最大范围内，作者不对因使用或无法使用本软件而产生的任何直接、间接、附带、特殊或后果性损失负责"
          "（包括数据丢失、设备损坏、业务中断、利润损失）。若法律强制要求承担责任，作者的总责任上限为你为本软件实际支付的金额"
          "（本软件免费提供，故为 0 元）。")
OLD_H9 = "9. 适用法律与联系"
OLD_W9 = ("本条款适用中华人民共和国法律（不含冲突规范）。如对条款有疑问，可通过你获取本软件的渠道联系作者 NesonCalo。"
          "本条款的最后更新日期为 2026 年 11 月 23 日。")

NEW_NOTE = "本条款提供多语言版本，以英文版本为权威文本；各语言译文仅为阅读便利，如与英文版本存在歧义，以英文版本为准。"
NEW_W6 = ("本软件按“现状”（AS IS）提供，不附带任何明示或默示的担保，包括但不限于适销性、特定用途适用性与不侵权担保。"
          "在适用法律允许的最大范围内，作者不对因使用或无法使用本软件而产生的任何直接、间接、附带、特殊或后果性损失负责"
          "（包括数据丢失、设备损坏、业务中断、利润损失）。本条不排除或限制你依所在地强制性法律享有的、不可通过合同放弃的权利；"
          "在无法排除责任的范围内，作者的总责任上限为你为本软件实际支付的金额（本软件免费提供，故为零）。")
NEW_H9 = "9. 适用法律与争议解决"
NEW_W9 = ("本条款的成立、效力、解释与履行，适用你所在地（若你代表组织使用本软件，则为该组织所在地）的法律，不适用其冲突规范；"
          "你所在地强制性消费者保护规定不受影响。因本条款产生的争议，双方应先善意协商；协商不成的，提交你所在地有管辖权的法院解决。"
          "如对条款有疑问，可通过你获取本软件的渠道或官网联系作者 NesonCalo。本条款最后更新日期为 2026 年 11 月 24 日。")

KEYS = [NEW_NOTE, NEW_W6, NEW_H9, NEW_W9]
OLD_KEYS = [OLD_NOTE, OLD_W6, OLD_H9, OLD_W9]

T = {}

T["en"] = [
    "These Terms are provided in multiple languages. The English version is the authoritative text; the translations are provided for convenience only, and if a translation differs from the English version, the English version prevails.",
    "The software is provided \"AS IS\", without any express or implied warranty, including but not limited to warranties of merchantability, fitness for a particular purpose and non-infringement. To the maximum extent permitted by applicable law, the author is not liable for any direct, indirect, incidental, special or consequential loss resulting from the use of, or inability to use, the software (including data loss, device damage, business interruption or lost profits). Nothing in this section excludes or limits rights that you have under mandatory law and that cannot be waived by contract; to the extent such liability cannot be excluded, the author's total liability is limited to the amount you actually paid for the software (the software is provided free of charge, so that amount is zero).",
    "9. Governing law and disputes",
    "The formation, validity, interpretation and performance of these Terms are governed by the laws of the place where you reside (or, if you use the software on behalf of an organisation, where that organisation is established), excluding its conflict-of-law rules; mandatory consumer-protection provisions of your place of residence remain unaffected. Any dispute arising from these Terms should first be addressed through good-faith negotiation; if that fails, it shall be submitted to the courts with jurisdiction at your place of residence. If you have questions about these Terms, you can reach the author NesonCalo through the channel where you obtained the software or the official website https://www.nesoncalo.com. These Terms were last updated on 24 November 2026.",
]

T["zh-CN"] = [NEW_NOTE, NEW_W6, NEW_H9, NEW_W9]

T["zh-TW"] = [
    "本條款提供多語言版本，以英文版本為權威文本；各語言譯本僅為閱讀便利，如與英文版本有歧義，以英文版本為準。",
    "本軟體按「現狀」（AS IS）提供，不附帶任何明示或默示的擔保，包括但不限於適銷性、特定用途適用性與不侵權擔保。在適用法律允許的最大範圍內，作者不對因使用或無法使用本軟體而產生的任何直接、間接、附帶、特殊或後果性損失負責（包括資料遺失、裝置損壞、業務中斷、利潤損失）。本條不排除或限制你依所在地強制性法律享有、且不可透過契約拋棄的權利；在無法排除責任的範圍內，作者的總責任上限為你為本軟體實際支付的金額（本軟體免費提供，故為零）。",
    "9. 適用法律與爭議解決",
    "本條款的成立、效力、解釋與履行，適用你所在地（若你代表組織使用本軟體，則為該組織所在地）的法律，不適用其衝突規範；你所在地強制性消費者保護規定不受影響。因本條款產生的爭議，雙方應先善意協商；協商不成的，提交你所在地有管轄權的法院解決。如對條款有疑問，可透過你取得本軟體的管道或官網 https://www.nesoncalo.com 聯絡作者 NesonCalo。本條款最後更新日期為 2026 年 11 月 24 日。",
]

T["zh-HK"] = [
    "本條款提供多語言版本，以英文版本為權威文本；各語言譯本僅為閱讀便利，如與英文版本有歧義，以英文版本為準。",
    "本軟件按「現狀」（AS IS）提供，不附帶任何明示或默示的擔保，包括但不限於適銷性、特定用途適用性與不侵權擔保。在適用法律允許的最大範圍內，作者不對因使用或無法使用本軟件而產生的任何直接、間接、附帶、特殊或後果性損失負責（包括資料遺失、裝置損壞、業務中斷、利潤損失）。本條不排除或限制你依所在地強制性法律享有、且不可透過合約放棄的權利；在無法排除責任的範圍內，作者的總責任上限為你為本軟件實際支付的金額（本軟件免費提供，故為零）。",
    "9. 適用法律與爭議解決",
    "本條款的成立、效力、解釋與履行，適用你所在地（若你代表組織使用本軟件，則為該組織所在地）的法律，不適用其衝突規範；你所在地強制性消費者保護規定不受影響。因本條款產生的爭議，雙方應先善意協商；協商不成的，提交你所在地有管轄權的法院解決。如對條款有疑問，可透過你取得本軟件的渠道或官網 https://www.nesoncalo.com 聯絡作者 NesonCalo。本條款最後更新日期為 2026 年 11 月 24 日。",
]

T["ja"] = [
    "本規約は多言語で提供されます。英語版が正文であり、各言語の翻訳は参照の便宜のみを目的とします。翻訳と英語版に相違がある場合は英語版が優先します。",
    "本ソフトウェアは「現状のまま（AS IS）」で提供され、明示または黙示のいかなる保証も伴いません。これには商品性、特定目的への適合性、権利非侵害の保証が含まれますが、これらに限りません。適用法が許す最大限の範囲で、作者は本ソフトウェアの使用または使用不能に起因する直接的、間接的、偶発的、特別または結果的損害（データの喪失、機器の損傷、業務の中断、逸失利益を含む）について責任を負いません。本条は、契約により放棄できない強行法規上のあなたの権利を排除または制限するものではありません。かかる責任を排除できない範囲では、作者の責任総額は、あなたが本ソフトウェアに対して実際に支払った金額を上限とします（本ソフトウェアは無償で提供されるため、その金額はゼロです）。",
    "9. 準拠法および紛争解決",
    "本規約の成立、効力、解釈および履行には、あなたの所在地（組織を代表して本ソフトウェアを使用する場合はその組織の所在地）の法律を、その抵触法を除いて適用します。あなたの所在地の強行的な消費者保護規定は影響を受けません。本規約から生じる紛争は、まず誠実に協議するものとし、協議が整わない場合はあなたの所在地の管轄裁判所に提起します。本規約についてご不明な点は、本ソフトウェアを入手した経路または公式サイト https://www.nesoncalo.com から作者 NesonCalo にご連絡ください。本規約の最終更新日は 2026 年 11 月 24 日です。",
]

T["ko"] = [
    "본 약관은 여러 언어로 제공됩니다. 영어 버전이 정본이며, 각 언어 번역본은 열람 편의를 위한 것입니다. 번역본과 영어 버전이 다를 경우 영어 버전이 우선합니다.",
    "본 소프트웨어는 \"있는 그대로(AS IS)\" 제공되며, 상품성, 특정 목적 적합성, 비침해를 포함하되 이에 국한되지 않는 명시적 또는 묵시적 보증을 제공하지 않습니다. 관련 법령이 허용하는 최대 범위에서, 작성자는 본 소프트웨어의 사용 또는 사용 불능으로 인한 직접적, 간접적, 부수적, 특별 또는 결과적 손해(데이터 손실, 기기 손상, 영업 중단, 이익 손실 포함)에 대해 책임지지 않습니다. 본 조항은 계약으로 포기할 수 없는 강행법상 귀하의 권리를 배제하거나 제한하지 않습니다. 그러한 책임을 배제할 수 없는 범위에서 작성자의 총 책임은 귀하가 본 소프트웨어에 실제로 지급한 금액으로 제한됩니다(본 소프트웨어는 무상으로 제공되므로 그 금액은 0입니다).",
    "9. 준거법 및 분쟁 해결",
    "본 약관의 성립, 효력, 해석 및 이행에는 귀하의 거주지(조직을 대표하여 사용하는 경우 해당 조직의 소재지)의 법률을 그 국제사법 규정을 제외하고 적용합니다. 귀하의 거주지의 강행적 소비자 보호 규정은 영향을 받지 않습니다. 본 약관으로 인한 분쟁은 먼저 선의로 협의하며, 협의가 이루어지지 않으면 귀하의 거주지의 관할 법원에 제기합니다. 본 약관에 관해 문의가 있으면 소프트웨어를 입수한 경로 또는 공식 웹사이트 https://www.nesoncalo.com 을 통해 작성자 NesonCalo 에게 연락할 수 있습니다. 본 약관의 최종 업데이트 날짜는 2026년 11월 24일입니다.",
]

T["de"] = [
    "Diese Bedingungen werden in mehreren Sprachen bereitgestellt. Maßgeblich ist die englische Fassung; die Übersetzungen dienen nur der besseren Lesbarkeit. Bei Abweichungen zwischen einer Übersetzung und der englischen Fassung gilt die englische Fassung.",
    "Die Software wird „wie besehen“ (AS IS) bereitgestellt, ohne ausdrückliche oder stillschweigende Gewährleistung, einschließlich, aber nicht beschränkt auf Gewährleistung der Marktgängigkeit, der Eignung für einen bestimmten Zweck und der Nichtverletzung von Rechten. Soweit gesetzlich zulässig, haftet der Autor nicht für unmittelbare, mittelbare, zufällige, besondere oder Folgeschäden (einschließlich Datenverlust, Geräteschaden, Betriebsunterbrechung oder entgangenem Gewinn), die aus der Nutzung oder der Unmöglichkeit der Nutzung der Software entstehen. Dieser Abschnitt schließt keine Rechte aus, die Ihnen nach zwingendem Recht zustehen und nicht durch Vertrag abbedungen werden können; soweit eine solche Haftung nicht ausgeschlossen werden kann, ist die Gesamthaftung des Autors auf den Betrag begrenzt, den Sie tatsächlich für die Software gezahlt haben (die Software wird kostenlos bereitgestellt, dieser Betrag ist daher null).",
    "9. Anwendbares Recht und Streitbeilegung",
    "Für Abschluss, Wirksamkeit, Auslegung und Erfüllung dieser Bedingungen gilt das Recht des Ortes, an dem Sie Ihren gewöhnlichen Aufenthalt haben (bei Nutzung im Namen einer Organisation: an dem diese niedergelassen ist), unter Ausschluss seiner Kollisionsnormen; zwingende Verbraucherschutzvorschriften Ihres Aufenthaltsorts bleiben unberührt. Streitigkeiten aus diesen Bedingungen sind zunächst gütlich zu verhandeln; gelingt dies nicht, sind sie den zuständigen Gerichten Ihres Aufenthaltsorts vorzulegen. Bei Fragen zu diesen Bedingungen erreichen Sie den Autor NesonCalo über den Kanal, über den Sie die Software bezogen haben, oder über die offizielle Website https://www.nesoncalo.com. Diese Bedingungen wurden zuletzt am 24. November 2026 aktualisiert.",
]

T["fr"] = [
    "Les présentes conditions sont fournies en plusieurs langues. La version anglaise fait foi ; les traductions ne sont fournies que pour faciliter la lecture et, en cas de divergence, la version anglaise prévaut.",
    "Le logiciel est fourni « en l'état » (AS IS), sans garantie expresse ou implicite, y compris, sans limitation, les garanties de qualité marchande, d'adéquation à un usage particulier et d'absence de contrefaçon. Dans toute la mesure permise par le droit applicable, l'auteur n'est pas responsable des pertes directes, indirectes, accessoires, spéciales ou consécutives (notamment perte de données, dommage matériel, interruption d'activité ou perte de bénéfices) résultant de l'utilisation ou de l'impossibilité d'utiliser le logiciel. La présente clause n'exclut ni ne limite les droits que vous tenez de dispositions légales impératives et auxquels vous ne pouvez renoncer par contrat ; dans la mesure où cette responsabilité ne peut être exclue, la responsabilité totale de l'auteur est limitée au montant que vous avez effectivement payé pour le logiciel (le logiciel étant fourni gratuitement, ce montant est nul).",
    "9. Droit applicable et litiges",
    "La formation, la validité, l'interprétation et l'exécution des présentes conditions sont régies par le droit du lieu où vous résidez (ou, si vous utilisez le logiciel pour le compte d'une organisation, du lieu où celle-ci est établie), à l'exclusion de ses règles de conflit de lois ; les dispositions impératives de protection des consommateurs de votre lieu de résidence demeurent applicables. Tout litige né des présentes conditions doit d'abord faire l'objet d'une négociation de bonne foi ; à défaut, il sera soumis aux tribunaux compétents de votre lieu de résidence. Pour toute question sur ces conditions, vous pouvez joindre l'auteur NesonCalo via le canal par lequel vous avez obtenu le logiciel ou le site officiel https://www.nesoncalo.com. Ces conditions ont été mises à jour pour la dernière fois le 24 novembre 2026.",
]

T["es"] = [
    "Estos términos se facilitan en varios idiomas. La versión inglesa es la versión auténtica; las traducciones solo se ofrecen por comodidad de lectura y, en caso de discrepancia, prevalece la versión inglesa.",
    "El software se proporciona «TAL CUAL» (AS IS), sin garantía expresa o implícita, incluidas, entre otras, las garantías de comerciabilidad, idoneidad para un fin concreto y no infracción. En la máxima medida permitida por la ley aplicable, el autor no responde de ningún daño directo, indirecto, incidental, especial o consecuente (incluidos la pérdida de datos, los daños al dispositivo, la interrupción del negocio o el lucro cesante) derivado del uso o de la imposibilidad de uso del software. Esta cláusula no excluye ni limita los derechos que le reconoce la legislación imperativa y que no pueden renunciarse por contrato; en la medida en que dicha responsabilidad no pueda excluirse, la responsabilidad total del autor se limita al importe que haya pagado efectivamente por el software (al ser gratuito, dicho importe es cero).",
    "9. Ley aplicable y controversias",
    "La formación, validez, interpretación y ejecución de estos términos se rigen por la ley del lugar en que usted reside (o, si utiliza el software en nombre de una organización, del lugar en que esta está establecida), con exclusión de sus normas de conflicto de leyes; las disposiciones imperativas de protección de los consumidores de su lugar de residencia seguirán siendo aplicables. Cualquier controversia derivada de estos términos deberá tratarse primero mediante negociación de buena fe; si esta fracasa, se someterá a los tribunales competentes de su lugar de residencia. Si tiene dudas sobre estos términos, puede contactar con el autor NesonCalo a través del canal por el que obtuvo el software o del sitio oficial https://www.nesoncalo.com. Estos términos se actualizaron por última vez el 24 de noviembre de 2026.",
]

T["it"] = [
    "I presenti termini sono forniti in più lingue. La versione inglese è quella autorevole; le traduzioni sono fornite solo per comodità di lettura e, in caso di divergenza, prevale la versione inglese.",
    "Il software è fornito «COSÌ COM'È» (AS IS), senza alcuna garanzia espressa o implicita, comprese, tra le altre, le garanzie di commerciabilità, idoneità a uno scopo particolare e non violazione di diritti altrui. Nella massima misura consentita dalla legge applicabile, l'autore non risponde di alcun danno diretto, indiretto, incidentale, speciale o consequenziale (inclusi perdita di dati, danni al dispositivo, interruzione dell'attività o perdita di profitto) derivante dall'uso o dall'impossibilità di usare il software. La presente clausola non esclude né limita i diritti che ti spettano in forza di norme imperative e che non possono essere derogati per contratto; nella misura in cui tale responsabilità non possa essere esclusa, la responsabilità complessiva dell'autore è limitata all'importo che hai effettivamente pagato per il software (il software è fornito gratuitamente, pertanto tale importo è zero).",
    "9. Legge applicabile e controversie",
    "La formazione, la validità, l'interpretazione e l'esecuzione dei presenti termini sono regolate dalla legge del luogo in cui risiedi (o, se usi il software per conto di un'organizzazione, del luogo in cui questa è stabilita), escluse le relative norme di conflitto; le disposizioni imperative a tutela dei consumatori del tuo luogo di residenza restano applicabili. Qualsiasi controversia derivante dai presenti termini dovrà essere dapprima affrontata con trattativa in buona fede; in caso di esito negativo, sarà sottoposta ai tribunali competenti del tuo luogo di residenza. Per domande sui presenti termini puoi contattare l'autore NesonCalo tramite il canale con cui hai ottenuto il software o il sito ufficiale https://www.nesoncalo.com. I presenti termini sono stati aggiornati l'ultima volta il 24 novembre 2026.",
]

T["pt-BR"] = [
    "Estes termos são fornecidos em vários idiomas. A versão em inglês é a versão oficial; as traduções servem apenas para facilitar a leitura e, em caso de divergência, prevalece a versão em inglês.",
    "O software é fornecido \"NO ESTADO EM QUE SE ENCONTRA\" (AS IS), sem qualquer garantia expressa ou implícita, incluindo, entre outras, as garantias de comercialização, adequação a uma finalidade específica e não violação de direitos. Na máxima extensão permitida pela lei aplicável, o autor não responde por qualquer perda direta, indireta, incidental, especial ou consequente (incluindo perda de dados, danos ao dispositivo, interrupção dos negócios ou lucros cessantes) decorrente do uso ou da impossibilidade de uso do software. Esta cláusula não exclui nem limita os direitos que você tem com base em normas imperativas e que não podem ser renunciados por contrato; na medida em que tal responsabilidade não possa ser excluída, a responsabilidade total do autor fica limitada ao valor que você efetivamente pagou pelo software (como o software é fornecido gratuitamente, esse valor é zero).",
    "9. Lei aplicável e controvérsias",
    "A formação, a validade, a interpretação e a execução destes termos são regidas pela lei do local onde você reside (ou, se usar o software em nome de uma organização, do local onde ela está estabelecida), excluindo suas normas de conflito de leis; as disposições imperativas de proteção ao consumidor do seu local de residência permanecem aplicáveis. Qualquer controvérsia decorrente destes termos deverá ser primeiro tratada por negociação de boa-fé; se esta falhar, será submetida aos tribunais competentes do seu local de residência. Em caso de dúvidas sobre estes termos, você pode contatar o autor NesonCalo pelo canal pelo qual obteve o software ou pelo site oficial https://www.nesoncalo.com. Estes termos foram atualizados pela última vez em 24 de novembro de 2026.",
]

T["ru"] = [
    "Настоящие Условия предоставляются на нескольких языках. Аутентичным текстом является английская версия; переводы предоставлены только для удобства чтения, и при расхождениях преимущественную силу имеет английская версия.",
    "Программное обеспечение предоставляется «КАК ЕСТЬ» (AS IS), без каких-либо явных или подразумеваемых гарантий, включая, но не ограничиваясь, гарантиями товарной пригодности, соответствия конкретной цели и отсутствия нарушений прав. В максимальной степени, допускаемой применимым правом, автор не несёт ответственности за любые прямые, косвенные, случайные, особые или последующие убытки (включая потерю данных, повреждение устройства, прерывание деятельности или упущенную выгоду), возникшие в результате использования или невозможности использования программного обеспечения. Настоящий раздел не исключает и не ограничивает права, предоставленные вам императивными нормами права, от которых нельзя отказаться договором; в той мере, в какой такая ответственность не может быть исключена, общая ответственность автора ограничивается суммой, фактически уплаченной вами за программное обеспечение (оно предоставляется бесплатно, поэтому эта сумма равна нулю).",
    "9. Применимое право и споры",
    "Заключение, действительность, толкование и исполнение настоящих Условий регулируются правом места вашего проживания (а если вы используете программное обеспечение от имени организации — правом места её учреждения), без учёта его коллизионных норм; императивные нормы о защите прав потребителей по месту вашего проживания сохраняют силу. Споры, возникающие из настоящих Условий, сначала должны разрешаться путём добросовестных переговоров; если это не удалось, они передаются в суды, обладающие юрисдикцией по месту вашего проживания. По вопросам об Условиях вы можете связаться с автором NesonCalo через канал, по которому получили программное обеспечение, или через официальный сайт https://www.nesoncalo.com. Условия обновлены 24 ноября 2026 г.",
]

T["ar"] = [
    "تُقدَّم هذه الشروط بعدة لغات. النص الإنجليزي هو النص المعتمد، وتُقدَّم الترجمات لتسهيل الاطلاع فقط، وفي حال وجود تعارض بين الترجمة والنص الإنجليزي تكون الأولوية للنص الإنجليزي.",
    "يُقدَّم البرنامج \"كما هو\" (AS IS) دون أي ضمان صريح أو ضمني، بما في ذلك على سبيل المثال لا الحصر ضمانات القابلية للتسويق والملاءمة لغرض معين وعدم المساس بحقوق الغير. إلى أقصى حد يسمح به القانون المطبق، لا يتحمل المؤلف أي مسؤولية عن أي خسارة مباشرة أو غير مباشرة أو عرضية أو خاصة أو تبعية (بما في ذلك فقدان البيانات أو تلف الجهاز أو تعطل الأعمال أو خسارة الأرباح) تنشأ عن استخدام البرنامج أو عدم إمكانية استخدامه. لا يستبعد هذا البند ولا يحد من الحقوق التي تكفلها لك القواعد الآمرة والتي لا يجوز التنازل عنها بالتعاقد؛ وإلى الحد الذي لا يمكن فيه استبعاد هذه المسؤولية، تقتصر المسؤولية الإجمالية للمؤلف على المبلغ الذي دفعته فعلاً مقابل البرنامج (وبما أن البرنامج يُقدَّم مجانًا فإن ذلك المبلغ صفر).",
    "9. القانون الحاكم وتسوية المنازعات",
    "تخضع نشأة هذه الشروط وصحتها وتفسيرها وتنفيذها لقانون المكان الذي تقيم فيه (أو المكان الذي يقع فيه مقر المنظمة إذا كنت تستخدم البرنامج باسمها)، باستثناء قواعده المتعلقة بتنازع القوانين؛ وتبقى الأحكام الآمرة لحماية المستهلك في محل إقامتك سارية. ويجب أولاً معالجة أي نزاع ينشأ عن هذه الشروط عبر التفاوض بحسن نية، وفي حال فشل ذلك يُحال النزاع إلى المحاكم المختصة في محل إقامتك. وإذا كانت لديك أسئلة عن هذه الشروط، يمكنك التواصل مع المؤلف NesonCalo عبر القناة التي حصلت منها على البرنامج أو الموقع الرسمي https://www.nesoncalo.com. وقد جرى آخر تحديث لهذه الشروط في 24 نوفمبر 2026.",
]

T["hi"] = [
    "ये शर्तें कई भाषाओं में उपलब्ध कराई गई हैं। अंग्रेज़ी संस्करण ही आधिकारिक पाठ है; अनुवाद केवल पढ़ने की सुविधा के लिए हैं और किसी अंतर की स्थिति में अंग्रेज़ी संस्करण मान्य होगा।",
    "यह सॉफ़्टवेयर \"जैसा है\" (AS IS) आधार पर उपलब्ध कराया गया है, बिना किसी स्पष्ट या अंतर्निहित वारंटी के, जिनमें बाज़ार-योग्यता, किसी विशेष उद्देश्य के लिए उपयुक्तता और अधिकार-उल्लंघन-रहित होने की वारंटी शामिल हैं, पर इन्हीं तक सीमित नहीं। लागू कानून द्वारा अनुमत अधिकतम सीमा तक, लेखक सॉफ़्टवेयर के उपयोग या उपयोग में असमर्थता से होने वाली किसी भी प्रत्यक्ष, अप्रत्यक्ष, आकस्मिक, विशेष या परिणामी हानि (डेटा हानि, डिवाइस क्षति, व्यवसाय बाधा या लाभ हानि सहित) के लिए उत्तरदायी नहीं है। यह अनुच्छेद उन अधिकारों को बाहर नहीं करता या सीमित नहीं करता जो आपको अनिवार्य कानून के अंतर्गत प्राप्त हैं और जिन्हें अनुबंध द्वारा छोड़ा नहीं जा सकता; जहाँ ऐसी उत्तरदायित्व को बाहर नहीं किया जा सकता, वहाँ लेखक का कुल उत्तरदायित्व उस राशि तक सीमित है जो आपने सॉफ़्टवेयर के लिए वास्तव में भुगतान की है (चूँकि सॉफ़्टवेयर निःशुल्क है, वह राशि शून्य है)।",
    "9. लागू कानून और विवाद",
    "इन शर्तों का गठन, वैधता, व्याख्या और निष्पादन उस स्थान के कानून द्वारा शासित होगा जहाँ आप निवास करते हैं (या, यदि आप किसी संगठन की ओर से सॉफ़्टवेयर का उपयोग करते हैं, तो जहाँ वह संगठन स्थापित है), उसके कानून-संघर्ष नियमों को छोड़कर; आपके निवास स्थान के अनिवार्य उपभोक्ता-संरक्षण प्रावधान प्रभावी रहेंगे। इन शर्तों से उत्पन्न कोई भी विवाद पहले सद्भावपूर्ण बातचीत से हल करने का प्रयास किया जाएगा; असफल होने पर इसे आपके निवास स्थान के सक्षम न्यायालयों के समक्ष प्रस्तुत किया जाएगा। इन शर्तों पर प्रश्न होने पर आप उस माध्यम से जिससे सॉफ़्टवेयर प्राप्त किया या आधिकारिक वेबसाइट https://www.nesoncalo.com के ज़रिए लेखक NesonCalo से संपर्क कर सकते हैं। ये शर्तें अंतिम बार 24 नवंबर 2026 को अद्यतन की गईं।",
]

T["bn"] = [
    "এই শর্তাবলি একাধিক ভাষায় প্রদান করা হয়েছে। ইংরেজি সংস্করণই প্রামাণ্য পাঠ; অনুবাদগুলো কেবল পড়ার সুবিধার জন্য, এবং কোনো পার্থক্য থাকলে ইংরেজি সংস্করণই প্রযোজ্য হবে।",
    "এই সফটওয়্যারটি \"যেমন আছে\" (AS IS) ভিত্তিতে প্রদান করা হয়েছে, কোনো প্রকাশ্য বা অন্তর্নিহিত ওয়্যারেন্টি ছাড়াই, যার মধ্যে বাণিজ্যিক উপযোগিতা, নির্দিষ্ট উদ্দেশ্যে উপযোগিতা এবং অধিকার-লঙ্ঘন-মুক্ত থাকার ওয়্যারেন্টি অন্তর্ভুক্ত কিন্তু সীমাবদ্ধ নয়। প্রযোজ্য আইন যতটা অনুমোদন করে, লেখক সফটওয়্যারের ব্যবহার বা ব্যবহারে অক্ষমতা থেকে উদ্ভূত কোনো প্রত্যক্ষ, পরোক্ষ, আকস্মিক, বিশেষ বা পরিণতিগত ক্ষতির (ডেটা হারানো, ডিভাইস ক্ষতি, ব্যবসায় বিঘ্ন বা মুনাফা হারানো সহ) জন্য দায়ী নন। এই ধারাটি আইনগতভাবে বাধ্যতামূলক এবং চুক্তির মাধ্যমে ছাড়া যায় না এমন আপনার অধিকার বাদ বা সীমিত করে না; যেখানে এমন দায় বাদ দেওয়া সম্ভব নয়, সেখানে লেখকের মোট দায় আপনার সফটওয়্যারের জন্য প্রকৃতপক্ষে প্রদত্ত অর্থের মধ্যে সীমাবদ্ধ (সফটওয়্যারটি বিনামূল্যে প্রদান করা হয়, তাই সেই অর্থ শূন্য)।",
    "9. প্রযোজ্য আইন ও বিরোধ",
    "এই শর্তাবলির গঠন, বৈধতা, ব্যাখ্যা ও সম্পাদন আপনি যে স্থানে বসবাস করেন (অথবা, কোনো প্রতিষ্ঠানের পক্ষে সফটওয়্যার ব্যবহার করলে, সেই প্রতিষ্ঠান যে স্থানে প্রতিষ্ঠিত) সেই স্থানের আইন দ্বারা পরিচালিত হবে, তার দ্বন্দ্ব-আইন বিধি বাদে; আপনার বসবাসস্থলের বাধ্যতামূলক ভোক্তা-সুরক্ষা বিধান কার্যকর থাকবে। এই শর্তাবলি থেকে উদ্ভূত কোনো বিরোধ প্রথমে সদিচ্ছাপূর্ণ আলোচনার মাধ্যমে নিষ্পত্তির চেষ্টা করা হবে; তা ব্যর্থ হলে আপনার বসবাসস্থলের এখতিয়ারসম্পন্ন আদালতে তা উপস্থাপন করা হবে। এই শর্তাবলি সম্পর্কে প্রশ্ন থাকলে আপনি যে মাধ্যম থেকে সফটওয়্যার পেয়েছেন বা অফিসিয়াল ওয়েবসাইট https://www.nesoncalo.com এর মাধ্যমে লেখক NesonCalo-এর সাথে যোগাযোগ করতে পারেন। এই শর্তাবলি সর্বশেষ ২৪ নভেম্বর ২০২৬-এ হালনাগাদ করা হয়েছে।",
]

T["vi"] = [
    "Các điều khoản này được cung cấp bằng nhiều ngôn ngữ. Bản tiếng Anh là bản có thẩm quyền; các bản dịch chỉ nhằm thuận tiện cho việc đọc, và nếu có khác biệt thì bản tiếng Anh được ưu tiên áp dụng.",
    "Phần mềm được cung cấp \"NGUYÊN TRẠNG\" (AS IS), không kèm bất kỳ bảo đảm rõ ràng hay ngụ ý nào, bao gồm nhưng không giới hạn ở các bảo đảm về khả năng thương mại, sự phù hợp cho một mục đích cụ thể và không xâm phạm quyền của bên thứ ba. Trong phạm vi tối đa mà pháp luật hiện hành cho phép, tác giả không chịu trách nhiệm đối với bất kỳ tổn thất trực tiếp, gián tiếp, ngẫu nhiên, đặc biệt hoặc hệ quả nào (bao gồm mất dữ liệu, hư hỏng thiết bị, gián đoạn kinh doanh hoặc mất lợi nhuận) phát sinh từ việc sử dụng hoặc không thể sử dụng phần mềm. Điều khoản này không loại trừ hay giới hạn các quyền mà bạn có theo quy định pháp luật bắt buộc và không thể từ bỏ bằng hợp đồng; trong phạm vi không thể loại trừ trách nhiệm đó, tổng trách nhiệm của tác giả được giới hạn ở số tiền bạn thực tế đã trả cho phần mềm (do phần mềm được cung cấp miễn phí nên số tiền đó bằng không).",
    "9. Luật áp dụng và tranh chấp",
    "Việc hình thành, hiệu lực, giải thích và thực hiện các điều khoản này được điều chỉnh bởi pháp luật nơi bạn cư trú (hoặc nơi tổ chức được thành lập nếu bạn sử dụng phần mềm thay mặt tổ chức), không kể các quy tắc xung đột pháp luật của nơi đó; các quy định bắt buộc về bảo vệ người tiêu dùng tại nơi bạn cư trú vẫn có hiệu lực. Mọi tranh chấp phát sinh từ các điều khoản này trước hết phải được giải quyết bằng thương lượng thiện chí; nếu không thành, sẽ được đưa ra các tòa án có thẩm quyền tại nơi bạn cư trú. Nếu có câu hỏi về các điều khoản này, bạn có thể liên hệ tác giả NesonCalo qua kênh mà bạn đã có được phần mềm hoặc trang web chính thức https://www.nesoncalo.com. Các điều khoản này được cập nhật lần cuối vào ngày 24 tháng 11 năm 2026.",
]

T["th"] = [
    "ข้อกำหนดเหล่านี้จัดทำในหลายภาษา ฉบับภาษาอังกฤษเป็นฉบับที่ใช้บังคับ ฉบับแปลมีไว้เพื่อความสะดวกในการอ่านเท่านั้น หากมีความแตกต่างกัน ให้ถือฉบับภาษาอังกฤษเป็นหลัก",
    "ซอฟต์แวร์นี้ให้บริการ \"ตามสภาพที่เป็นอยู่\" (AS IS) โดยไม่มีการรับประกันใด ๆ ทั้งโดยชัดแจ้งหรือโดยปริยาย รวมถึงแต่ไม่จำกัดเพียงการรับประกันเรื่องคุณภาพตามมาตรฐานการค้า ความเหมาะสมต่อวัตถุประสงค์เฉพาะ และการไม่ละเมิดสิทธิของผู้อื่น ภายในขอบเขตสูงสุดที่กฎหมายที่ใช้บังคับอนุญาต ผู้เขียนไม่รับผิดชอบต่อความสูญเสียใด ๆ ทั้งทางตรง ทางอ้อม โดยบังเอิญ พิเศษ หรือเป็นผลสืบเนื่อง (รวมถึงข้อมูลสูญหาย อุปกรณ์เสียหาย ธุรกิจหยุดชะงัก หรือสูญเสียกำไร) ที่เกิดจากการใช้หรือไม่สามารถใช้ซอฟต์แวร์นี้ ข้อนี้ไม่ตัดหรือจำกัดสิทธิที่คุณมีตามกฎหมายที่เป็นบทบังคับซึ่งไม่อาจสละได้โดยสัญญา ในขอบเขตที่ไม่สามารถยกเว้นความรับผิดดังกล่าวได้ ความรับผิดรวมของผู้เขียนจำกัดอยู่ที่จำนวนเงินที่คุณชำระจริงสำหรับซอฟต์แวร์นี้ (เนื่องจากซอฟต์แวร์ให้บริการฟรี จำนวนดังกล่าวจึงเป็นศูนย์)",
    "9. กฎหมายที่ใช้บังคับและข้อพิพาท",
    "การก่อตั้ง ความสมบูรณ์ การตีความ และการปฏิบัติตามข้อกำหนดเหล่านี้อยู่ภายใต้กฎหมายของถิ่นที่คุณพำนักอาศัย (หรือถิ่นที่องค์กรตั้งอยู่ หากคุณใช้ซอฟต์แวร์ในนามขององค์กร) โดยไม่รวมกฎหมายว่าด้วยการขัดกันแห่งกฎหมายของถิ่นนั้น ข้อกำหนดบังคับเกี่ยวกับการคุ้มครองผู้บริโภค ณ ถิ่นที่คุณพำนักยังคงมีผลใช้บังคับ ข้อพิพาทใด ๆ ที่เกิดจากข้อกำหนดเหล่านี้ควรได้รับการแก้ไขด้วยการเจรจาโดยสุจริตก่อน หากไม่สำเร็จให้ยื่นต่อศาลที่มีเขตอำนาจ ณ ถิ่นที่คุณพำนัก หากมีข้อสงสัยเกี่ยวกับข้อกำหนดเหล่านี้ คุณสามารถติดต่อผู้เขียน NesonCalo ผ่านช่องทางที่คุณได้รับซอฟต์แวร์หรือเว็บไซต์ทางการ https://www.nesoncalo.com ข้อกำหนดเหล่านี้ได้รับการปรับปรุงล่าสุดเมื่อวันที่ 24 พฤศจิกายน 2026",
]

T["id"] = [
    "Ketentuan ini tersedia dalam beberapa bahasa. Versi bahasa Inggris adalah versi yang berwenang; terjemahan hanya untuk kemudahan membaca dan, jika terdapat perbedaan, versi bahasa Inggris yang berlaku.",
    "Perangkat lunak ini disediakan \"SEBAGAIMANA ADANYA\" (AS IS), tanpa jaminan tersurat maupun tersirat, termasuk namun tidak terbatas pada jaminan kelayakan jual, kesesuaian untuk tujuan tertentu, dan tidak melanggar hak pihak lain. Sejauh diizinkan oleh hukum yang berlaku, penulis tidak bertanggung jawab atas segala kerugian langsung, tidak langsung, insidental, khusus, atau konsekuensial (termasuk kehilangan data, kerusakan perangkat, gangguan usaha, atau kehilangan keuntungan) yang timbul dari penggunaan atau ketidakmampuan menggunakan perangkat lunak ini. Pasal ini tidak mengecualikan atau membatasi hak yang Anda miliki berdasarkan hukum yang bersifat memaksa dan tidak dapat dikesampingkan melalui kontrak; sejauh tanggung jawab tersebut tidak dapat dikecualikan, total tanggung jawab penulis dibatasi pada jumlah yang benar-benar Anda bayarkan untuk perangkat lunak ini (karena perangkat lunak disediakan gratis, jumlah tersebut adalah nol).",
    "9. Hukum yang berlaku dan sengketa",
    "Pembentukan, keabsahan, penafsiran, dan pelaksanaan Ketentuan ini diatur oleh hukum tempat Anda berdomisili (atau, jika Anda menggunakan perangkat lunak atas nama organisasi, tempat organisasi itu didirikan), tidak termasuk kaidah pertentangan hukumnya; ketentuan wajib tentang perlindungan konsumen di tempat domisili Anda tetap berlaku. Setiap sengketa yang timbul dari Ketentuan ini harus terlebih dahulu diselesaikan melalui perundingan dengan itikad baik; jika gagal, sengketa diajukan kepada pengadilan yang berwenang di tempat domisili Anda. Jika Anda memiliki pertanyaan tentang Ketentuan ini, Anda dapat menghubungi penulis NesonCalo melalui saluran tempat Anda memperoleh perangkat lunak ini atau situs resmi https://www.nesoncalo.com. Ketentuan ini terakhir diperbarui pada 24 November 2026.",
]

T["tr"] = [
    "Bu koşullar birden çok dilde sunulmaktadır. Yetkili metin İngilizce sürümüdür; çeviriler yalnızca okuma kolaylığı içindir ve bir farklılık olması hâlinde İngilizce sürüm geçerlidir.",
    "Yazılım \"OLDUĞU GİBİ\" (AS IS) sunulur; satılabilirlik, belirli bir amaca uygunluk ve hak ihlalinde bulunmama garantileri dâhil ancak bunlarla sınırlı olmamak üzere açık veya zımni hiçbir garanti verilmez. Yürürlükteki hukukun izin verdiği azami ölçüde yazar; yazılımın kullanılmasından veya kullanılamamasından doğan doğrudan, dolaylı, arızi, özel veya dolaylı zararlardan (veri kaybı, cihaz hasarı, iş kesintisi veya kâr kaybı dâhil) sorumlu tutulamaz. Bu madde, emredici hukuktan doğan ve sözleşmeyle feragat edilemeyecek haklarınızı ortadan kaldırmaz veya sınırlamaz; bu sorumluluğun hariç tutulamadığı ölçüde yazarın toplam sorumluluğu, yazılım için fiilen ödediğiniz tutarla sınırlıdır (yazılım ücretsiz sunulduğu için bu tutar sıfırdır).",
    "9. Uygulanacak hukuk ve uyuşmazlıklar",
    "Bu koşulların kuruluşu, geçerliliği, yorumlanması ve ifası; ikamet ettiğiniz yerin (bir kuruluş adına kullanıyorsanız o kuruluşun kurulduğu yerin) hukukuna, kanunlar ihtilafı kuralları hariç olmak üzere tabidir; ikamet yerinizdeki emredici tüketici koruma hükümleri saklıdır. Bu koşullardan doğan uyuşmazlıklar öncelikle iyi niyetli müzakerelerle çözülmeye çalışılır; bu başarısız olursa, ikamet yerinizdeki yetkili mahkemelere başvurulur. Bu koşullarla ilgili sorularınız için yazılımı edindiğiniz kanal veya https://www.nesoncalo.com resmî sitesi aracılığıyla yazar NesonCalo ile iletişim kurabilirsiniz. Bu koşullar en son 24 Kasım 2026 tarihinde güncellenmiştir.",
]

T["nl"] = [
    "Deze voorwaarden worden in meerdere talen aangeboden. De Engelse versie is de authentieke tekst; de vertalingen dienen alleen voor leesgemak en bij tegenstrijdigheid prevaleert de Engelse versie.",
    "De software wordt \"ZOALS ZIJ IS\" (AS IS) geleverd, zonder enige expliciete of impliciete garantie, met inbegrip van, maar niet beperkt tot, garanties van verkoopbaarheid, geschiktheid voor een bepaald doel en niet-inbreuk. Voor zover toegestaan door toepasselijk recht is de auteur niet aansprakelijk voor enig direct, indirect, incidenteel, bijzonder of gevolgschade (waaronder gegevensverlies, schade aan apparatuur, bedrijfsstoring of gederfde winst) die voortvloeit uit het gebruik of het niet kunnen gebruiken van de software. Deze bepaling sluit geen rechten uit die u op grond van dwingend recht heeft en die niet bij overeenkomst kunnen worden afgestaan, en beperkt die ook niet; voor zover dergelijke aansprakelijkheid niet kan worden uitgesloten, is de totale aansprakelijkheid van de auteur beperkt tot het bedrag dat u daadwerkelijk voor de software heeft betaald (aangezien de software gratis wordt geleverd, is dat bedrag nul).",
    "9. Toepasselijk recht en geschillen",
    "Het tot stand komen, de geldigheid, de uitleg en de uitvoering van deze voorwaarden worden beheerst door het recht van de plaats waar u uw gewone verblijfplaats heeft (of, als u de software namens een organisatie gebruikt, waar die organisatie is gevestigd), met uitsluiting van de conflictenrechtelijke regels daarvan; dwingende bepalingen inzake consumentenbescherming van uw verblijfplaats blijven van toepassing. Geschillen die uit deze voorwaarden voortkomen, moeten eerst te goeder trouw worden onderhandeld; lukt dat niet, dan worden zij voorgelegd aan de bevoegde rechter van uw verblijfplaats. Bij vragen over deze voorwaarden kunt u de auteur NesonCalo bereiken via het kanaal waarlangs u de software heeft verkregen of via de officiële website https://www.nesoncalo.com. Deze voorwaarden zijn laatst bijgewerkt op 24 november 2026.",
]

T["pl"] = [
    "Niniejsze warunki są udostępniane w wielu językach. Wersją autentyczną jest wersja angielska; tłumaczenia mają jedynie ułatwić lekturę, a w razie rozbieżności pierwszeństwo ma wersja angielska.",
    "Oprogramowanie jest udostępniane \"TAK, JAK JEST\" (AS IS), bez jakichkolwiek gwarancji wyraźnych lub dorozumianych, w tym w szczególności gwarancji przydatności handlowej, przydatności do określonego celu i nie naruszania praw osób trzecich. W maksymalnym zakresie dopuszczalnym przez obowiązujące prawo autor nie odpowiada za jakiekolwiek szkody bezpośrednie, pośrednie, przypadkowe, szczególne lub następcze (w tym utratę danych, uszkodzenie urządzenia, przerwę w działalności lub utracone korzyści) wynikające z korzystania z oprogramowania lub niemożności korzystania z niego. Niniejsza klauzula nie wyłącza ani nie ogranicza praw przysługujących Ci na podstawie przepisów bezwzględnie obowiązujących, których nie można zrzec się w umowie; w zakresie, w jakim takiej odpowiedzialności nie można wyłączyć, łączna odpowiedzialność autora jest ograniczona do kwoty, którą rzeczywiście zapłaciłeś za oprogramowanie (ponieważ jest ono udostępniane bezpłatnie, kwota ta wynosi zero).",
    "9. Prawo właściwe i spory",
    "Zawarcie, ważność, wykładnia i wykonanie niniejszych warunków podlegają prawu miejsca Twojego zamieszkania (a jeśli używasz oprogramowania w imieniu organizacji — prawu miejsca jej siedziby), z wyłączeniem jego norm kolizyjnych; bezwzględnie obowiązujące przepisy o ochronie konsumentów w miejscu Twojego zamieszkania pozostają w mocy. Spory wynikające z niniejszych warunków należy najpierw rozwiązywać w drodze negocjacji w dobrej wierze; jeśli się nie powiedzie, spór zostanie przekazany sądom właściwym dla miejsca Twojego zamieszkania. W razie pytań dotyczących niniejszych warunków możesz skontaktować się z autorem NesonCalo za pośrednictwem kanału, przez który uzyskałeś oprogramowanie, lub przez oficjalną stronę https://www.nesoncalo.com. Niniejsze warunki zostały ostatnio zaktualizowane 24 listopada 2026 r.",
]

T["uk"] = [
    "Ці Умови надаються кількома мовами. Автентичним текстом є англійська версія; переклади надані лише для зручності читання, і в разі розбіжностей переважає англійська версія.",
    "Програмне забезпечення надається «ЯК Є» (AS IS), без будь-яких явних або неявних гарантій, зокрема, але не обмежуючись гарантіями придатності до продажу, відповідності конкретній меті та відсутності порушень прав. У максимальному обсязі, дозволеному застосовним правом, автор не несе відповідальності за будь-які прямі, непрямі, випадкові, особливі або похідні збитки (зокрема втрату даних, пошкодження пристрою, перерву в діяльності чи втрачену вигоду), що виникають внаслідок використання або неможливості використання програмного забезпечення. Цей розділ не виключає й не обмежує прав, які ви маєте згідно з імперативними нормами права і від яких не можна відмовитися договором; у тій мірі, у якій таку відповідальність неможливо виключити, загальна відповідальність автора обмежується сумою, яку ви фактично сплатили за програмне забезпечення (оскільки воно надається безкоштовно, ця сума дорівнює нулю).",
    "9. Застосовне право та спори",
    "Укладення, чинність, тлумачення та виконання цих Умов регулюються правом місця вашого проживання (а якщо ви використовуєте програмне забезпечення від імені організації — правом місця її заснування), без урахування його колізійних норм; імперативні норми про захист прав споживачів за місцем вашого проживання зберігають чинність. Спори, що виникають з цих Умов, спершу мають вирішуватися шляхом добросовісних переговорів; якщо це не вдалося, вони передаються до судів, що мають юрисдикцію за місцем вашого проживання. З питань щодо цих Умов ви можете зв’язатися з автором NesonCalo через канал, яким ви отримали програмне забезпечення, або через офіційний сайт https://www.nesoncalo.com. Ці Умови востаннє оновлено 24 листопада 2026 р.",
]

T["fa"] = [
    "این شرایط به چند زبان ارائه می‌شود. متن انگلیسی نسخه معتبر است؛ ترجمه‌ها تنها برای سهولت مطالعه‌اند و در صورت اختلاف، نسخه انگلیسی حاکم است.",
    "این نرم‌افزار «همان‌گونه که هست» (AS IS) ارائه می‌شود و هیچ ضمانت صریح یا ضمنی، از جمله ضمانت قابلیت تجاری، تناسب برای هدفی خاص و عدم نقض حقوق دیگران، همراه ندارد. در حداکثر حدی که قانون قابل اجرا اجازه می‌دهد، نویسنده در قبال هیچ زیان مستقیم، غیرمستقیم، اتفاقی، خاص یا تبعی (از جمله از دست رفتن داده‌ها، آسیب به دستگاه، توقف کسب‌وکار یا از دست رفتن سود) که از استفاده یا ناتوانی در استفاده از نرم‌افزار ناشی شود مسئول نیست. این بند حقوقی را که بر اساس قوانین آمره برای شما وجود دارد و قابل اسقاط با قرارداد نیست، حذف یا محدود نمی‌کند؛ در حدی که چنین مسئولیتی قابل حذف نباشد، مسئولیت کلی نویسنده محدود به مبلغی است که واقعاً برای نرم‌افزار پرداخت کرده‌اید (چون نرم‌افزار رایگان ارائه می‌شود، آن مبلغ صفر است).",
    "9. قانون حاکم و حل اختلاف",
    "ایجاد، اعتبار، تفسیر و اجرای این شرایط تابع قانون محل اقامت شماست (یا اگر نرم‌افزار را به نام سازمانی استفاده می‌کنید، محل استقرار آن سازمان)، بدون قواعد تعارض قوانین آن؛ مقررات آمره حمایت از مصرف‌کننده در محل اقامت شما همچنان جاری است. هر اختلاف ناشی از این شرایط باید نخست از طریق مذاکره با حسن نیت حل شود؛ در صورت عدم موفقیت، به دادگاه‌های صالح محل اقامت شما ارجاع می‌شود. اگر درباره این شرایط پرسشی دارید، می‌توانید از طریق همان مجرایی که نرم‌افزار را به دست آورده‌اید یا وب‌سایت رسمی https://www.nesoncalo.com با نویسنده NesonCalo در تماس باشید. این شرایط آخرین بار در ۲۴ نوامبر ۲۰۲۶ به‌روزرسانی شده است.",
]

T["ms"] = [
    "Terma ini disediakan dalam beberapa bahasa. Versi bahasa Inggeris ialah teks yang berwibawa; terjemahan hanya untuk kemudahan membaca dan jika terdapat perbezaan, versi bahasa Inggeris terpakai.",
    "Perisian ini disediakan \"SEBAGAIMANA ADANYA\" (AS IS), tanpa sebarang waranti nyata atau tersirat, termasuk tetapi tidak terhad kepada waranti kebolehdagangan, kesesuaian untuk tujuan tertentu dan tidak melanggar hak pihak ketiga. Setakat maksimum yang dibenarkan oleh undang-undang yang terpakai, pengarang tidak bertanggungjawab atas sebarang kerugian langsung, tidak langsung, sampingan, khas atau berbangkit (termasuk kehilangan data, kerosakan peranti, gangguan perniagaan atau kehilangan keuntungan) yang timbul daripada penggunaan atau ketidakupayaan menggunakan perisian ini. Fasal ini tidak mengecualikan atau mengehadkan hak yang anda miliki di bawah undang-undang wajib yang tidak boleh dilepaskan melalui kontrak; setakat tanggungjawab tersebut tidak boleh dikecualikan, jumlah tanggungjawab pengarang terhad kepada amaun yang sebenarnya anda bayar untuk perisian ini (kerana perisian disediakan secara percuma, amaun itu ialah sifar).",
    "9. Undang-undang yang terpakai dan pertikaian",
    "Pembentukan, kesahihan, tafsiran dan pelaksanaan Terma ini ditadbir oleh undang-undang tempat anda bermastautin (atau, jika anda menggunakan perisian bagi pihak organisasi, tempat organisasi itu ditubuhkan), tidak termasuk peraturan percanggahan undang-undangnya; peruntukan wajib perlindungan pengguna di tempat mastautin anda kekal berkuat kuasa. Sebarang pertikaian yang timbul daripada Terma ini hendaklah terlebih dahulu diselesaikan melalui rundingan dengan niat baik; jika gagal, pertikaian hendaklah dikemukakan kepada mahkamah yang berbidang kuasa di tempat mastautin anda. Jika anda mempunyai soalan tentang Terma ini, anda boleh menghubungi pengarang NesonCalo melalui saluran tempat anda memperoleh perisian ini atau laman web rasmi https://www.nesoncalo.com. Terma ini kali terakhir dikemas kini pada 24 November 2026.",
]

T["sv"] = [
    "Dessa villkor ges på flera språk. Den engelska versionen är den auktoritativa texten; översättningarna är endast för läsbarhet och vid skillnader gäller den engelska versionen.",
    "Programvaran levereras \"I BEFINTLIGT STÅND\" (AS IS), utan någon uttrycklig eller underförstådd garanti, inklusive men inte begränsat till garantier om säljbarhet, lämplighet för ett visst ändamål och icke-intrång. I den största utsträckning som tillämplig lag tillåter är författaren inte ansvarig för någon direkt, indirekt, tillfällig, särskild eller följdskada (inklusive dataförlust, enhetsskada, driftavbrott eller utebliven vinst) som uppstår genom användning av eller oförmåga att använda programvaran. Detta avsnitt utesluter eller begränsar inte rättigheter som du har enligt tvingande lag och som inte kan avtalas bort; i den utsträckning sådant ansvar inte kan uteslutas är författarens totala ansvar begränsat till det belopp du faktiskt betalat för programvaran (eftersom programvaran är gratis är detta belopp noll).",
    "9. Tillämplig lag och tvister",
    "Dessa villkors tillkomst, giltighet, tolkning och utförande regleras av lagen på den plats där du har hemvist (eller, om du använder programvaran för en organisations räkning, där organisationen är etablerad), med undantag för dess lagvalsregler; tvingande konsumentskyddsbestämmelser på din hemvistort gäller fortfarande. Tvister som uppstår ur dessa villkor ska först hanteras genom förhandling i god tro; om detta misslyckas ska de hänskjutas till de domstolar som har jurisdiktion på din hemvistort. Vid frågor om dessa villkor kan du nå författaren NesonCalo via den kanal genom vilken du fick programvaran eller via den officiella webbplatsen https://www.nesoncalo.com. Dessa villkor uppdaterades senast den 24 november 2026.",
]


def main():
    missing = []
    for code in sorted(os.listdir(LOCALES)):
        if not code.endswith(".json"):
            continue
        lang = code[:-5]
        path = os.path.join(LOCALES, code)
        with io.open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        vals = T.get(lang)
        if not vals:
            missing.append(lang)
            continue
        for k in OLD_KEYS:
            data.pop(k, None)
        for k, v in zip(KEYS, vals):
            data[k] = v
        with io.open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=1)
            fp.write("\n")
    print("updated locales:", len(T), "missing:", missing)

    with io.open(INDEX, "r", encoding="utf-8") as fp:
        html = fp.read()
    for old, new in zip(OLD_KEYS, KEYS):
        cnt = html.count(old)
        html = html.replace(old, new)
        print("replaced", cnt, "->", new[:24])
    with io.open(INDEX, "w", encoding="utf-8") as fp:
        fp.write(html)


if __name__ == "__main__":
    main()
